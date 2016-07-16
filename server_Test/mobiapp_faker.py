#!/usr/bin/python
#coding:utf-8
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#

import optparse
import random
import time

from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import ReconnectingClientFactory, Protocol
from twisted.internet import reactor
from twisted.internet import task
from twisted.internet import stdio
from twisted.protocols import basic

from message_base import *
from RsRobot_enum_pb2 import *
from RsRobot_pb2 import *
import gen_uid

g_options = None

class MobiApp:
    connector = None
    service = None
    cui = None
    protocol = None
    control = None

class MobiAppProtocol(Protocol):
    def __init__(self):
        self.mq = MQ()

    def connectionMade(self):
        print "INFO: [connectionMade] peer: ", self.transport.getPeer()
        self.transport.setTcpKeepAlive(1)
        MobiApp.protocol = self
        MobiApp.service.send_online_request()

    def dataReceived(self, data):
        print "INFO: [dataReceived] Received bytes: %d" % len(data)
        self.mq.AppendData(data)
        self.mq.Apply(self.handle_message)

    def connectionLost(self, reason):
        print "INFO: [connectionLost] Connection lost: %s" % reason.getErrorMessage()
        MobiApp.protocol = None
        self.transport.loseConnection()

    def handle_message(self, msg):
        print "Handle message: ", msg.Header()
        MobiApp.service.handle_message(msg)

    def send_response(self, hdr, rsp):
        self.send_message(hdr, rsp)

    def send_message(self, hdr, msg):
        msg_data = ""
        if msg is not None:
            msg_data = msg.SerializeToString()
        hdr.length = hdr.LENGTH + len(msg_data)
        hdr_data = hdr.pack()
        print "Send message: ", hdr
        self.transport.write(hdr_data)
        if len(msg_data) > 0:
            self.transport.write(msg_data)


class MobiAppProtocolFactory(ReconnectingClientFactory):
    protocol = MobiAppProtocol

    def clientConnectionFailed(self, connector, reason):
        print "INFO: [clientConnectionLost] Connection failed: %s" % reason.getErrorMessage()

    def clientConnectionLost(self, connector, reason):
        #print "INFO: [clientConnectionLost] Connection lost: %s" % reason.getErrorMessage()
        pass


class MobiAppService(object):
    def __init__(self):
        self.ctype = MOBIAPP

        self.username = None
        self.password = None
        self.sessionid = ""
        self.uid = 0;
        self.requested_authcode = False

        self.devinfo_list = [] 
        #self.uid_gen = gen_uid.UIDGenerator("fc:aa:14:e5:f0:10")
        self.uid_gen = gen_uid.UIDGenerator()

        self.timer_periodic = 60  # seconds
        self.heartbeat_timer = task.LoopingCall(self.heartbeat_sender)

    def show_status(self):
        print "connected: ", "true" if MobiApp.protocol else "false"
        print "username: ", self.username
        print "password: ", self.password
        print "sessionid: ", self.sessionid
        print "uid: ", self.uid
        print "heartbeat timer periodic: %d, status: %s" % (self.timer_periodic, "running" if self.heartbeat_timer.running else "stopped")
        print "requested_authcode: ", self.requested_authcode
        print "devinfo list: "
        for devinfo in self.devinfo_list:
            print devinfo

    def get_next_seq(self):
        return self.uid_gen.get_uid()

    def biz_type_to_cmd(self, biz_type):
        if biz_type == "authcode_login":
            return USER_LOGIN_BY_AUTHCODE_REQ
        elif biz_type == "reset_password":
            return USER_RESET_PASSWORD_REQ
        elif biz_type == "register":
            return USER_REGISTER_REQ
        else:
            return None

    def heartbeat_sender(self):
        self.send_heartbeat_request()

    def enable_heartbeat(self):
        self.heartbeat_timer.start(self.timer_periodic);
        print "enabled"

    def disable_heartbeat(self):
        self.heartbeat_timer.stop()
        print "disabled"

    def send_message(self, hdr, body, req_desc):
        if MobiApp.protocol:
            MobiApp.protocol.send_message(hdr, body)
            print "Sent %s request, seq no: %x" % (req_desc, hdr.seq)
            return True
        else:
            print "Connection not available, please connect first"
            return False

    def send_common_message_request(self, cid, did, cmd, req_desc):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = cid 
        hdr.did = did 
        hdr.seq = self.get_next_seq();
        hdr.cmd = cmd
        self.send_message(hdr, None, req_desc)

    def send_request_authcode_request(self, username, biz_type):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = 0
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_REQUEST_AUTHCODE_REQ
        body = UserRequestAuthCodeParams()
        body.type = 1   # by mobile phone
        body.username = username
        biz_cmd = self.biz_type_to_cmd(biz_type)
        if biz_cmd is None:
            print "Unknown biz_type: ", biz_type
            return
        body.biz_cmd = biz_cmd
        self.send_message(hdr, body, "user request auth code")

    def send_login_by_authcode_request(self, username, authcode):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = 0
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_LOGIN_BY_AUTHCODE_REQ
        body = UserLoginByAuthCodeParams()
        body.username = self.username = username
        body.authcode = authcode
        self.send_message(hdr, body, "user login by auth code")

    def send_login_request(self, username, password):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = 0
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_LOGIN_REQ
        body = UserLoginParams()
        body.username = self.username = username
        body.password = self.password = password
        self.send_message(hdr, body, "user login")

    def send_logout_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_LOGOUT_REQ
        body = UserLogoutParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        self.send_message(hdr, body, "user logout")

    def send_online_request(self):
        self.send_common_message_request(self.uid, 0, CLIENT_ONLINE_REQ, "user online")

    def send_heartbeat_request(self):
        self.send_common_message_request(self.uid, 0, CLIENT_HEARTBEAT_REQ, "heartbeat")

    def send_register_auth_request(self, username):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = 0 
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_REGISTER_AUTH_REQ
        body = UserRegisterAuthParams()
        body.type = MOBILE
        body.username = self.username = username
        self.send_message(hdr, body, "user register auth")

    def send_register_request(self, username, password, authcode):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = 0 
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_REGISTER_REQ
        body = UserRegisterParams()
        body.username = username
        body.password = password
        body.authcode = authcode
        self.send_message(hdr, body, "user register")

    def send_change_password_request(self, new_password):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_CHANGE_PASSWORD_REQ
        body = UserChangePasswordParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        body.old_pwd = self.password
        body.new_pwd = new_password
        self.send_message(hdr, body, "user change password")

    def send_reset_password_request(self, username, authcode, new_password):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = 0
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_RESET_PASSWORD_REQ
        body = UserResetPasswordParams()
        body.username = username
        body.authcode = authcode
        body.new_pwd = new_password
        self.send_message(hdr, body, "user reset password")

    def send_modify_profile_request(self, params):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_MODIFY_PROFILE_REQ
        body = UserModifyProfileParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        body.profile.nickname = "Yuu"
        body.profile.sex = 1
        body.profile.age = 18
        body.profile.job = "IT"
        self.send_message(hdr, body, "user modify profile")

    def send_get_profile_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq()
        hdr.cmd = USER_GET_PROFILE_REQ
        body = UserGetProfileParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        self.send_message(hdr, body, "user get profile")

    def send_add_device_request(self, devsn):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_ADD_DEVICE_REQ
        body = UserAddDeviceParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        body.devsn = devsn
        self.send_message(hdr, body, "user add device")

    def send_del_device_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_DEL_DEVICE_REQ
        body = UserDeleteDeviceParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        body.devid = devid 
        self.send_message(hdr, body, "user delete device")

    def send_get_device_list_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_GET_DEVICE_LIST_REQ
        body = UserGetDeviceListParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        self.send_message(hdr, body, "user get device list")

    def send_modify_device_alias_request(self, devid, alias):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_MODIFY_DEVICE_ALIAS_REQ
        body = UserModifyDeviceAliasParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        body.devid = devid
        body.alias = alias
        self.send_message(hdr, body, "user modify device alias")

    def send_change_default_device_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = USER_CHANGE_DEFAULT_DEVICE_REQ
        body = UserChangeDefaultDeviceParams()
        body.uid = self.uid
        body.sessionid = self.sessionid
        body.dft_devid = devid
        self.send_message(hdr, body, "user change default device")

    def send_device_charge_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_CHARGE_REQ
        body = DeviceChargeParams()
        body.enable = 1
        self.send_message(hdr, body, "device charge")

    def send_device_areaclean_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_AREA_CLEAN_REQ
        body = DeviceAreaCleanParams()
        body.enable = 1
        body.area_num = 2
        #body.area_id_list = [1, 2, 3]
        self.send_message(hdr, body, "device area clean")

    def send_device_autoclean_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_AUTO_CLEAN_REQ
        body = DeviceAutoCleanParams()
        body.enable = 1
        body.pause = 2
        body.clean_type = 2
        self.send_message(hdr, body, "device auto clean")

    def send_device_manual_ctrl_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_MANUAL_CTRL_REQ
        body = DeviceManualCtrlParams()
        body.enable = 1
        body.angle_speed = 2
        body.speed = 2
        body.clean_enable = 2
        self.send_message(hdr, body, "device manual ctrl")

    def send_device_navigate_move_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_NAVIGATE_MOVE_REQ
        body = DeviceNavigateMoveParams()
        body.enable = 1
        body.x = 2.2
        body.y = 2.1
        self.send_message(hdr, body, "device navigate move")

    def send_device_point_clean_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_POINT_CLEAN_REQ
        body = DevicePointCleanParams()
        body.enable = 1
        self.send_message(hdr, body, "device point clean")

    def send_device_config_reset_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_CONFIG_RESET_REQ
        self.send_message(hdr, None, "device config reset")

    def send_device_wifi_ctrl_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_WIFI_CTRL_REQ
        body = DeviceWIFICtrlParams()
        body.mode = 1
        self.send_message(hdr, body, "device wifi ctrl")

    def send_get_order_list_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_ORDERLIST_GETTING_REQ
        self.send_message(hdr, None, "device order list getting")

    def send_set_order_list_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_ORDERLIST_SETTING_REQ
        body = CleanOrderParams()
        body.weekday_list.append(1)
        body.weekday_list.append(3)
        body.weekday_list.append(5)
        body.day_time = int(time.time())
        self.send_message(hdr, body, "device order list setting")

    def send_get_vwall_list_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_VWALL_LIST_GETTING_REQ
        self.send_message(hdr, None, "device vwall list getting")

    def send_set_vwall_list_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_VWALL_LIST_SETTING_REQ
        body = VirtualWallList()
        vw = VirtualWall()
        vw.enable = 1
        vw.start_x = 1
        vw.start_y = 1
        vw.end_x = 2
        vw.end_y = 2
        body.vwall_list.append(vw)
        self.send_message(hdr, body, "device vwall list setting")

    def send_get_area_clean_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_AREACLEAN_INFO_GETTING_REQ
        self.send_message(hdr, None, "device get area clean")

    def send_map_ctrl_request(self, devid, map_type):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq()
        hdr.cmd = DEVICE_MAP_CTRL_REQ
        body = DeviceMapCtrlParams()
        body.broadcast = 1
        body.map_type = map_type
        self.send_message(hdr, body, "device map ctrl")

    def send_map_lidar_ctrl_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq()
        hdr.cmd = DEVICE_MAP_LIDAR_CTRL_REQ
        body = DeviceLidarCtrlParams()
        body.frequency = 30
        self.send_message(hdr, body, "map lidar ctrl")

    def send_device_upgrade_ctrl_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid 
        hdr.seq = self.get_next_seq()
        hdr.cmd = DEVICE_UPGRADE_CTRL_REQ
        body = DeviceUpgradeCtrlParams()
        body.cmd = 1
        body.value = 2
        self.send_message(hdr, body, "device upgrade ctrl")

    def send_device_control_lock_request(self, devid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid
        hdr.seq = self.get_next_seq()
        hdr.cmd = DEVICE_CONTROL_LOCK_REQ
        self.send_message(hdr, None, "device control lock")

    def send_query_device_data_request(self, devid, req_type, start_time, end_time):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid
        hdr.seq = self.get_next_seq()
        hdr.cmd = req_type
        body = QueryDeviceHistoryDataParams()
        body.sessionid = self.sessionid
        body.start_time = start_time
        body.end_time = end_time
        self.send_message(hdr, body, "query device historical data")

    def send_query_device_cleanmap_request(self, devid, taskid):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.uid
        hdr.did = devid
        hdr.seq = self.get_next_seq()
        hdr.cmd = QUERY_DEVICE_CLEANMAP_REQ
        body = QueryCleanMapParams()
        body.sessionid = self.sessionid
        body.taskid = taskid
        self.send_message(hdr, body, "query clean map")

    def handle_message(self, msg):
        hdr = MessageHeader()
        if msg.Header().cmd == USER_REQUEST_AUTHCODE_RSP:
            self.handle_user_request_authcode_response(msg)
        elif msg.Header().cmd == USER_LOGIN_BY_AUTHCODE_RSP:
            self.handle_user_login_by_authcode_response(msg)
        elif msg.Header().cmd == USER_LOGIN_RSP:
            self.handle_user_login_response(msg)
        elif msg.Header().cmd == USER_LOGOUT_RSP:
            self.handle_user_logout_response(msg)
        elif msg.Header().cmd == USER_REGISTER_AUTH_RSP:
            self.handle_user_register_auth_response(msg)
        elif msg.Header().cmd == USER_REGISTER_RSP:
            self.handle_user_register_response(msg)
        elif msg.Header().cmd == CLIENT_ONLINE_RSP:
            self.handle_client_online_response(msg)
        elif msg.Header().cmd == CLIENT_HEARTBEAT_RSP:
            self.handle_client_heartbeat_response(msg)
        elif msg.Header().cmd == USER_CHANGE_PASSWORD_RSP:
            self.handle_change_password_response(msg)
        elif msg.Header().cmd == USER_RESET_PASSWORD_RSP:
            self.handle_reset_password_response(msg)
        elif msg.Header().cmd == USER_MODIFY_PROFILE_RSP:
            self.handle_modify_profile_response(msg)
        elif msg.Header().cmd == USER_GET_PROFILE_RSP:
            self.handle_get_profile_response(msg)
        elif msg.Header().cmd == USER_ADD_DEVICE_RSP:
            self.handle_add_device_response(msg)
        elif msg.Header().cmd == USER_DEL_DEVICE_RSP:
            self.handle_del_device_response(msg)
        elif msg.Header().cmd == USER_GET_DEVICE_LIST_RSP:
            self.handle_get_device_list_response(msg)
        elif msg.Header().cmd == USER_MODIFY_DEVICE_ALIAS_RSP:
            self.handle_modify_device_alias_response(msg)
        elif msg.Header().cmd == USER_CHANGE_DEFAULT_DEVICE_RSP:
            self.handle_change_default_device_response(msg)
        elif msg.Header().cmd == DEVICE_INFO_GETTING_RSP:
            self.handle_get_device_info_response(msg)
        elif msg.Header().cmd == DEVICE_STATUS_GETTING_RSP:
            self.handle_get_device_status_response(msg)
        elif msg.Header().cmd == DEVICE_WLAN_INFO_GETTING_RSP:
            self.handle_get_device_wlan_info_response(msg)
        elif msg.Header().cmd == DEVICE_SN_GETTING_RSP:
            self.handle_get_device_sn_response(msg)
        elif msg.Header().cmd == DEVICE_CHARGE_RSP:
            self.handle_device_charge_response(msg)
        elif msg.Header().cmd == DEVICE_AREA_CLEAN_RSP:
            self.handle_device_areaclean_response(msg)
        elif msg.Header().cmd == DEVICE_AUTO_CLEAN_RSP:
            self.handle_device_autoclean_response(msg)
        elif msg.Header().cmd == DEVICE_MANUAL_CTRL_RSP:
            self.handle_device_manual_ctrl_response(msg)
        elif msg.Header().cmd == DEVICE_NAVIGATE_MOVE_RSP:
            self.handle_device_navigate_move_response(msg)
        elif msg.Header().cmd == DEVICE_POINT_CLEAN_RSP:
            self.handle_device_point_clean_response(msg)
        elif msg.Header().cmd == DEVICE_CONFIG_RESET_RSP:
            self.handle_device_config_reset_response(msg)
        elif msg.Header().cmd == DEVICE_WIFI_CTRL_RSP:
            self.handle_device_wifi_ctrl_response(msg)
        elif msg.Header().cmd == DEVICE_ORDERLIST_GETTING_RSP:
            self.handle_device_get_orderlist_response(msg)
        elif msg.Header().cmd == DEVICE_ORDERLIST_SETTING_RSP:
            self.handle_device_set_orderlist_response(msg)
        elif msg.Header().cmd == DEVICE_VWALL_LIST_GETTING_RSP:
            self.handle_device_get_vwall_list_response(msg)
        elif msg.Header().cmd == DEVICE_VWALL_LIST_SETTING_RSP:
            self.handle_device_set_vwall_list_response(msg)
        elif msg.Header().cmd == DEVICE_AREACLEAN_INFO_GETTING_RSP:
            self.handle_device_get_areaclean_info_response(msg)
        elif msg.Header().cmd == DEVICE_MAP_GLOBAL_DATA or \
                msg.Header().cmd == DEVICE_MAP_LIDAR_DATA or \
                msg.Header().cmd == DEVICE_MAP_PATH_DATA or \
                msg.Header().cmd == DEVICE_MAP_POSITION_DATA:
            self.handle_device_map_ctrl_response(msg)
        elif msg.Header().cmd == DEVICE_UPGRADE_CTRL_RSP:
            self.handle_device_upgrade_ctrl_response(msg)
        elif msg.Header().cmd == DEVICE_UPGRADE_PACKAGE_INFO_RSP:
            self.handle_device_upgrade_progress_info_response(msg)
        elif msg.Header().cmd == DEVICE_UPGRADE_PROGRESS_INFO_RSP:
            self.handle_device_upgrade_progress_info_response(msg)
        elif msg.Header().cmd == DEVICE_CONTROL_LOCK_RSP:
            self.handle_device_control_lock_response(msg)
        elif msg.Header().cmd == QUERY_DEVICE_CLEANINFO_RSP:
            self.handle_query_clean_info_response(msg)
        elif msg.Header().cmd == QUERY_DEVICE_CLEANMAP_RSP:
            self.handle_query_clean_map_response(msg)
        elif msg.Header().cmd == QUERY_DEVICE_KEY_EVENT_RSP:
            self.handle_query_key_event_response(msg)
        elif msg.Header().cmd == QUERY_DEVICE_FAULT_EVENT_RSP:
            self.handle_query_fault_event_response(msg)
        elif msg.Header().cmd == USER_KICKOUT_CMD:
            self.handle_user_kickout_cmd(msg)
        elif msg.Header().cmd == DEVICE_EVENT_REPORT_FAULT:
            self.handle_fault_event_report(msg)
        elif msg.Header().cmd == DEVICE_EVENT_REPORT_KEY:
            self.handle_key_event_report(msg)
        elif msg.Header().cmd == DEVICE_EVENT_REPORT_CLEANTASK:
            self.handle_cleantask_event_report(msg)
        elif msg.Header().cmd == DEVICE_EVENT_REPORT_CLEANMAP:
            self.handle_cleanmap_event_report(msg)
        else:
            print "Unknown message: %s" % msg.Header()

        MobiApp.cui.transport.write(">>> ")


    def handle_user_request_authcode_response(self, msg):
        print "[UserRequestAuthCodeResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_user_login_by_authcode_response(self, msg):
        print "[UserLoginByAuthCodeResponse]"
        self.handle_user_login_response(msg)

    def handle_reset_password_response(self, msg):
        print "[UserResetPasswordResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_user_login_response(self, msg):
        print "[UserLoginResponse]"
        rsp = UserLoginResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.uid = rsp.attrs.uid
            self.sessionid = rsp.attrs.sessionid
        print rsp

    def handle_user_logout_response(self, msg):
        print "[UserLogoutResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.sessionid = ""
            self.uid = 0
            self.devinfo_list = []
        print rsp

    def handle_user_register_auth_response(self, msg):
        print "[UserRegisterAuthResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.requested_authcode = True
        print rsp

    def handle_user_register_response(self, msg):
        print "[UserRegisterResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_client_online_response(self, msg):
        print "[MobiAppOnlineResponse]"
        print "  Empty Params"

    def handle_client_heartbeat_response(self, msg):
        print "[MobiAppHeartbeatResponse]"
        print "  Empty Params"

    def handle_change_password_response(self, msg):
        print "[UserChangePasswordResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_modify_profile_response(self, msg):
        print "[UserModifyProfileResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_get_profile_response(self, msg):
        print "[UserGetProfileResponse]"
        rsp = UserGetProfileResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            print "  User get profile SUCCESS"
            print "  { nickname: %s, sex: %s, age: %d, job: %s }" % (rsp.profile.nickname, "male" if rsp.profile.sex == 1 else "female", rsp.profile.age, rsp.profile.job)
        else:
            print "  error code: %s" % rsp.errcode
            print "  error str: %s" % rsp.errstr

    def handle_add_device_response(self, msg):
        print "[UserAddDeviceResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_del_device_response(self, msg):
        print "[UserDeleteDeviceResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_get_device_list_response(self, msg):
        print "[UserGetDeviceListResponse]"
        rsp = UserGetDeviceListResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.devinfo_list = []
            if len(rsp.attrs.udi_list) == 0:
                print "No devices"
            else:
                for devinfo in rsp.attrs.udi_list:
                    devinfo_str = " { devsn: %s, devid: %d, ctime: %d, status: %d, alias: %s, is_default: %s }" % \
                            (devinfo.devsn, devinfo.devid, devinfo.ctime, devinfo.status, devinfo.alias if devinfo.alias else "", "true" if devinfo.is_default else "false")
                    print devinfo_str
                    self.devinfo_list.append(devinfo_str)
        else:
            print "  error code: %s" % rsp.errcode
            print "  error str: %s" % rsp.errstr

    def handle_modify_device_alias_response(self, msg):
        print "[UserModifyDeviceAliasResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_change_default_device_response(self, msg):
        print "[UserChangeDefaultDeviceResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_get_device_info_response(self, msg):
        print "[UserGetDeviceInfoResponse]"
        rsp = DeviceInfoGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_get_device_status_response(self, msg):
        print "[UserGetDeviceStatusResponse]"
        rsp = DeviceStatusGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_get_device_wlan_info_response(self, msg):
        print "[UserGetDeviceWLANInfoResponse]"
        rsp = DeviceWLANInfoGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_get_device_sn_response(self, msg):
        print "[UserGetDeviceSNResponse]"
        rsp = DeviceSnGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_charge_response(self, msg):
        print "[DeviceChargeResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_areaclean_response(self, msg):
        print "[DeviceAreaCleanResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_autoclean_response(self, msg):
        print "[DeviceAutoCleanResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_manual_ctrl_response(self, msg):
        print "[DeviceManualCtrlResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_navigate_move_response(self, msg):
        print "[DeviceNavigateMoveResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_point_clean_response(self, msg):
        print "[DevicePointCleanResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_config_reset_response(self, msg):
        print "[DeviceConfigResetResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_wifi_ctrl_response(self, msg):
        print "[DeviceWifiCtrlResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_get_orderlist_response(self, msg):
        print "[DeviceCleanOrderListGettingResponse]"
        rsp = DeviceCleanOrderListGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_set_orderlist_response(self, msg):
        print "[DeviceCleanOrderListSettingResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_get_vwall_list_response(self, msg):
        print "[DeviceVWallListGettingResponse]"
        rsp = DeviceVirtualWallListGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_set_vwall_list_response(self, msg):
        print "[DeviceVWallListSettingResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_get_areaclean_info_response(self, msg):
        print "[DeviceAreaCleanInfoGettingResponse]"
        rsp = DeviceAreaCleanGettingResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_map_ctrl_response(self, msg):
        print "[DeviceMapCtrlResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_upgrade_ctrl_response(self, msg):
        print "[DeviceUpgradeCtrlResponse]"
        rsp = DeviceUpgradeCtrlResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_upgrade_package_info_response(self, msg):
        print "[DeviceUpgradePackageInfoResponse]"
        rsp = DeviceUpgradePackageInfo()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_upgrade_progress_info_response(self, msg):
        print "[DeviceUpgradeProgressInfoResponse]"
        rsp = DeviceUpgradeProgressInfo()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_device_control_lock_response(self, msg):
        print "[DeviceControlLockResponse]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_query_clean_info_response(self, msg):
        print "[QueryCleanInfoResponse]"
        rsp = QueryCleanInfoResult()
        rsp.ParseFromString(msg.Payload())
        cleaninfo_size = len(rsp.cleaninfo_list.cleaninfo)
        if cleaninfo_size < 20:
            print rsp
        else:
            print "NOTE: cleaninfo more than 20, only print the size: ", cleaninfo_size

    def handle_query_clean_map_response(self, msg):
        print "[QueryCleanMapResponse]"
        rsp = QueryCleanMapResult()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_query_key_event_response(self, msg):
        print "[QueryKeyEventResponse]"
        rsp = QueryKeyEventResult()
        rsp.ParseFromString(msg.Payload())
        keyevent_size = len(rsp.keyevent_list.keyevent)
        if keyevent_size < 20:
            print rsp
        else:
            print "NOTE: keyevent more than 20, only print the size: ", keyevent_size

    def handle_query_fault_event_response(self, msg):
        print "[QueryFaultEventResponse]"
        rsp = QueryFaultEventResult()
        rsp.ParseFromString(msg.Payload())
        faultevent_size = len(rsp.faultevent_list.faultevent)
        if faultevent_size < 20:
            print rsp
        else:
            print "NOTE: faultevent more than 20, only print the size: ", faultevent_size

    def handle_user_kickout_cmd(self, msg):
        print "[UserKickoutCmd]"
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.sessionid = ""
        self.devinfo_list = []
        print rsp

    def handle_fault_event_report(self, msg):
        print "[FaultEventReport]"
        rsp = DeviceFaultEventReportParams()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_key_event_report(self, msg):
        print "[KeyEventReport]"
        rsp = DeviceKeyEventReportParams()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_cleantask_event_report(self, msg):
        print "[CleanTaskEventReport]"
        rsp = DeviceCleanTaskReportParams()
        rsp.ParseFromString(msg.Payload())
        print rsp

    def handle_cleanmap_event_report(self, msg):
        print "[CleanMapEventReport]"
        rsp = DeviceMapReportParams()
        rsp.ParseFromString(msg.Payload())
        print rsp

class Control:
    def __init__(self):
        self.cmd = None
        self.cmd_params = None

    def handleCommand(self, cmd, params):
        self.cmd = cmd
        self.params = params
        self.run()

    def run(self):
        if self.cmd in ["exit", "quit"]:
            reactor.stop()
        elif self.cmd in ["help", "?"]:
            MobiApp.cui.showHelp(self.params)
        elif self.cmd == "connect":
            if MobiApp.protocol is not None:
                print "Connection was connected"
            else:
                MobiApp.connector.connect()
        elif self.cmd == "disconnect":
            MobiApp.connector.disconnect()
        elif self.cmd == "enable_heartbeat":
            MobiApp.service.enable_heartbeat()
        elif self.cmd == "disable_heartbeat":
            MobiApp.service.disable_heartbeat()
        elif self.cmd == "client_online":
            MobiApp.service.send_online_request()
        elif self.cmd == "status":
            MobiApp.service.show_status()
        elif self.cmd == "request_authcode":
            username = self.params[0]
            biz_type = self.params[1]
            MobiApp.service.send_request_authcode_request(username, biz_type)
        elif self.cmd == "login_by_authcode":
            username = self.params[0]
            authcode = self.params[1]
            MobiApp.service.send_login_by_authcode_request(username, authcode)
        elif self.cmd == "login":
            username = self.params[0]
            password = self.params[1]
            MobiApp.service.send_login_request(username, password)
        elif self.cmd == "logout":
            if len(MobiApp.service.sessionid) == 0:
                print "You are not login"
            else:
                MobiApp.service.send_logout_request()
        elif self.cmd == "register_auth":
            if len(MobiApp.service.sessionid) > 0:
                print "You are logged in, please logout first for user registration"
            else:
                username = self.params[0]
                MobiApp.service.send_register_auth_request(username)
        elif self.cmd == "register":
            if MobiApp.service.requested_authcode:
                print "username: ", MobiApp.service.username
                username = MobiApp.service.username
                password = self.params[0]
                authcode = self.params[1]
                MobiApp.service.send_register_request(username, password, authcode)
            else:
                print "You are not request auth code, please request auth code by command [register_auth] first"
        elif self.cmd == "change_password":
            if MobiApp.service.password is None:
                print "Please login first"
            else:
                new_password = self.params[0]
                MobiApp.service.send_change_password_request(new_password)
        elif self.cmd == "reset_password":
            username = self.params[0]
            authcode = self.params[1]
            new_password = self.params[2]
            MobiApp.service.send_reset_password_request(username, authcode, new_password)
        elif self.cmd == "modify_profile":
            MobiApp.service.send_modify_profile_request(self.params)
        elif self.cmd == "get_profile":
            MobiApp.service.send_get_profile_request()
        elif self.cmd == "add_device":
            devsn = self.params[0]
            MobiApp.service.send_add_device_request(devsn)
        elif self.cmd == "del_device":
            devid = int(self.params[0])
            MobiApp.service.send_del_device_request(devid)
        elif self.cmd == "get_device_list":
            MobiApp.service.send_get_device_list_request()
        elif self.cmd == "modify_device_alias":
            devid = int(self.params[0])
            alias = self.params[1]
            MobiApp.service.send_modify_device_alias_request(devid, alias)
        elif self.cmd == "set_default_device":
            devid = int(self.params[0])
            MobiApp.service.send_change_default_device_request(devid)
        elif self.cmd == "get_device_info":
            uid = MobiApp.service.uid
            devid = int(self.params[0])
            MobiApp.service.send_common_message_request(uid, devid, DEVICE_INFO_GETTING_REQ, self.cmd)
        elif self.cmd == "get_device_status":
            uid = MobiApp.service.uid
            devid = int(self.params[0])
            MobiApp.service.send_common_message_request(uid, devid, DEVICE_STATUS_GETTING_REQ, self.cmd)
        elif self.cmd == "get_device_wlan_info":
            uid = MobiApp.service.uid
            devid = int(self.params[0])
            MobiApp.service.send_common_message_request(uid, devid, DEVICE_WLAN_INFO_GETTING_REQ, self.cmd)
        elif self.cmd == "get_device_sn":
            uid = MobiApp.service.uid
            devid = int(self.params[0])
            MobiApp.service.send_common_message_request(uid, devid, DEVICE_SN_GETTING_REQ, self.cmd)
        elif self.cmd == "device_charge":
            devid = int(self.params[0])
            MobiApp.service.send_device_charge_request(devid)
        elif self.cmd == "device_area_clean":
            devid = int(self.params[0])
            MobiApp.service.send_device_areaclean_request(devid)
        elif self.cmd == "device_auto_clean":
            devid = int(self.params[0])
            MobiApp.service.send_device_autoclean_request(devid)
        elif self.cmd == "device_manual_ctrl":
            devid = int(self.params[0])
            MobiApp.service.send_device_manual_ctrl_request(devid)
        elif self.cmd == "device_navigate_move":
            devid = int(self.params[0])
            MobiApp.service.send_device_navigate_move_request(devid)
        elif self.cmd == "device_point_clean":
            devid = int(self.params[0])
            MobiApp.service.send_device_point_clean_request(devid)
        elif self.cmd == "device_config_reset":
            devid = int(self.params[0])
            MobiApp.service.send_device_config_reset_request(devid)
        elif self.cmd == "device_wifi_ctrl":
            devid = int(self.params[0])
            MobiApp.service.send_device_wifi_ctrl_request(devid)
        elif self.cmd == "get_order_list":
            devid = int(self.params[0])
            MobiApp.service.send_get_order_list_request(devid)
        elif self.cmd == "set_order_list":
            devid = int(self.params[0])
            MobiApp.service.send_set_order_list_request(devid)
        elif self.cmd == "get_vwall_list":
            devid = int(self.params[0])
            MobiApp.service.send_get_vwall_list_request(devid)
        elif self.cmd == "set_vwall_list":
            devid = int(self.params[0])
            MobiApp.service.send_set_vwall_list_request(devid)
        elif self.cmd == "get_area_clean_info":
            devid = int(self.params[0])
            MobiApp.service.send_get_area_clean_request(devid)
        elif self.cmd == "map_ctrl":
            devid = int(self.params[0])
            map_type = int(self.params[1])
            MobiApp.service.send_map_ctrl_request(devid, map_type)
        elif self.cmd == "map_lidar_ctrl":
            devid = int(self.params[0])
            MobiApp.service.send_map_lidar_ctrl_request(devid)
        elif self.cmd == "device_upgrade_ctrl":
            devid = int(self.params[0])
            MobiApp.service.send_device_upgrade_ctrl_request(devid)
        elif self.cmd == "device_control_lock":
            devid = int(self.params[0])
            MobiApp.service.send_device_control_lock_request(devid)
        elif self.cmd == "query_clean_info":
            devid = int(self.params[0])
            start_time = int(self.params[1])
            end_time = int(self.params[2])
            MobiApp.service.send_query_device_data_request(devid, QUERY_DEVICE_CLEANINFO_REQ, start_time, end_time)
        elif self.cmd == "query_clean_map":
            devid = int(self.params[0])
            taskid = int(self.params[1])
            MobiApp.service.send_query_device_cleanmap_request(devid, taskid)
        elif self.cmd == "query_key_event":
            devid = int(self.params[0])
            start_time = int(self.params[1])
            end_time = int(self.params[2])
            MobiApp.service.send_query_device_data_request(devid, QUERY_DEVICE_KEY_EVENT_REQ, start_time, end_time)
        elif self.cmd == "query_fault_event":
            devid = int(self.params[0])
            start_time = int(self.params[1])
            end_time = int(self.params[2])
            MobiApp.service.send_query_device_data_request(devid, QUERY_DEVICE_FAULT_EVENT_REQ, start_time, end_time)
        else:
            print "Unknown command: ", self.cmd


class CUI(basic.LineReceiver):
    from os import linesep as delimiter

    commands_help = \
            { \
            '?'                       : '? [COMMAND]', \
            'help'                    : 'help [COMMAND]', \
            'exit'                    : 'exit', \
            'quit'                    : 'quit', \
            'connect'                 : 'connect', \
            'disconnect'              : 'disconnect', \
            'enable_heartbeat'        : 'enable_heartbeat', \
            'disable_heartbeat'       : 'disable_heartbeat', \
            'status'                  : 'status', \
            'client_online'           : 'client_online', \
            'request_authcode'        : 'request_authcode <USERNAME> <authcode_login | reset_password>', \
            'login_by_authcode'       : 'login_by_authcode <USERNAME> <AUTH CODE>', \
            'login'                   : 'login <USERNAME> <PASSWORD>', \
            'logout'                  : 'logout', \
            'register_auth'           : 'register_auth <USERNAME>', \
            'register'                : 'register <PASSOWRD> <AUTH CODE>', \
            'change_password'         : 'change_password <NEW PASSOWRD>', \
            'reset_password'          : 'reset_password <USERNAME> <AUTH CODE> <NEW PASSOWRD>', \
            'modify_profile'          : 'modify_profile', \
            'get_profile'             : 'get_profile', \
            'add_device'              : 'add_device <DEVICE SN>',\
            'del_device'              : 'del_device <DEVICE ID>',\
            'get_device_list'         : 'get_device_list',\
            'modify_device_alias'     : 'modify_device_alias <DEVICE ID> <ALIAS>',\
            'set_default_device'      : 'set_default_device <DEVICE ID>',\
            'get_device_info'         : 'get_device_info <DEVICE ID>',\
            'get_device_status'       : 'get_device_status <DEVICE ID>',\
            'get_device_wlan_info'    : 'get_device_wlan_info <DEVICE ID>',\
            'get_device_sn'           : 'get_device_sn <DEVICE ID>',\
            'device_charge'           : 'device_charge <DEVICE ID>',\
            'device_area_clean'       : 'device_area_clean <DEVICE ID>',\
            'device_auto_clean'       : 'device_auto_clean <DEVICE ID>',\
            'device_manual_ctrl'      : 'device_manual_ctrl <DEVICE ID>',\
            'device_navigate_move'    : 'device_navigate_move <DEVICE ID>',\
            'device_point_clean'      : 'device_point_clean <DEVICE ID>',\
            'device_config_reset'     : 'device_config_reset <DEVICE ID>',\
            'device_wifi_ctrl'        : 'device_wifi_ctrl <DEVICE ID>',\
            'get_order_list'          : 'get_order_list <DEVICE ID>',\
            'set_order_list'          : 'set_order_list <DEVICE ID>',\
            'get_vwall_list'          : 'get_vwall_list <DEVICE ID>',\
            'set_vwall_list'          : 'set_vwall_list <DEVICE ID>',\
            'get_area_clean_info'     : 'get_area_clean_info <DEVICE ID>',\
            'map_ctrl'                : 'map_ctrl <DEVICE ID> <MAP_TYPE>',\
            'map_lidar_ctrl'          : 'map_lidar_ctrl <DEVICE ID>',\
            'device_upgrade_ctrl'     : 'device_upgrade_ctrl <DEVICE ID>',\
            'device_control_lock'     : 'device_control_lock <DEVICE ID>',\
            'query_clean_info'        : 'query_clean_info <DEVICE ID> <START TIME> <END TIME>',\
            'query_clean_map'         : 'query_clean_map <DEVICE ID> <TASK ID>',\
            'query_key_event'         : 'query_key_event <DEVICE ID> <START TIME> <END TIME>',\
            'query_fault_event'       : 'query_fault_event <DEVICE ID> <START TIME> <END TIME>',\
            }
    help = \
"Commands: \n\
  ?                      : %s\n\
  help                   : %s\n\
  exit                   : %s\n\
  quit                   : %s\n\
  connect                : %s\n\
  disconnect             : %s\n\
  enable_heartbeat       : %s\n\
  disable_heartbeat      : %s\n\
  client_online          : %s\n\
  status                 : %s\n\
  request_authcode       : %s\n\
  login_by_authcode      : %s\n\
  login                  : %s\n\
  logout                 : %s\n\
  register_auth          : %s\n\
  register               : %s\n\
  change_password        : %s\n\
  reset_password         : %s\n\
  modify_profile         : %s\n\
  get_profile            : %s\n\
  add_device             : %s\n\
  del_device             : %s\n\
  get_device_list        : %s\n\
  modify_device_alias    : %s\n\
  set_default_device     : %s\n\
  get_device_info        : %s\n\
  get_device_status      : %s\n\
  get_device_wlan_info   : %s\n\
  get_device_sn          : %s\n\
  device_charge          : %s\n\
  device_area_clean      : %s\n\
  device_auto_clean      : %s\n\
  device_manual_ctrl     : %s\n\
  device_navigate_move   : %s\n\
  device_point_clean     : %s\n\
  device_config_reset    : %s\n\
  device_wifi_ctrl       : %s\n\
  get_order_list         : %s\n\
  set_order_list         : %s\n\
  get_vwall_list         : %s\n\
  set_vwall_list         : %s\n\
  get_area_clean_info    : %s\n\
  map_ctrl               : %s\n\
  map_lidar_ctrl         : %s\n\
  device_upgrade_ctrl    : %s\n\
  device_control_lock    : %s\n\
  query_clean_info       : %s\n\
  query_clean_map        : %s\n\
  query_key_event        : %s\n\
  query_fault_event      : %s\n\
  " % (\
  commands_help['?'],\
  commands_help['help'],\
  commands_help['exit'],\
  commands_help['quit'],\
  commands_help['connect'],\
  commands_help['disconnect'],\
  commands_help['enable_heartbeat'],\
  commands_help['disable_heartbeat'],\
  commands_help['client_online'],\
  commands_help['status'],\
  commands_help['request_authcode'],\
  commands_help['login_by_authcode'],\
  commands_help['login'],\
  commands_help['logout'],\
  commands_help['register_auth'],\
  commands_help['register'],\
  commands_help['change_password'],\
  commands_help['reset_password'],\
  commands_help['modify_profile'],\
  commands_help['get_profile'],\
  commands_help['add_device'],\
  commands_help['del_device'],\
  commands_help['get_device_list'],\
  commands_help['modify_device_alias'],\
  commands_help['set_default_device'],\
  commands_help['get_device_info'],\
  commands_help['get_device_status'],\
  commands_help['get_device_wlan_info'],\
  commands_help['get_device_sn'],\
  commands_help['device_charge'],\
  commands_help['device_area_clean'],\
  commands_help['device_auto_clean'],\
  commands_help['device_manual_ctrl'],\
  commands_help['device_navigate_move'],\
  commands_help['device_point_clean'],\
  commands_help['device_config_reset'],\
  commands_help['device_wifi_ctrl'],\
  commands_help['get_order_list'],\
  commands_help['set_order_list'],\
  commands_help['get_vwall_list'],\
  commands_help['set_vwall_list'],\
  commands_help['get_area_clean_info'],\
  commands_help['map_ctrl'],\
  commands_help['map_lidar_ctrl'],\
  commands_help['device_upgrade_ctrl'],\
  commands_help['device_control_lock'],\
  commands_help['query_clean_info'],\
  commands_help['query_clean_map'],\
  commands_help['query_key_event'],\
  commands_help['query_fault_event'],\
  )

    def connectionMade(self):
        self.transport.write('>>> ')

    def lineReceived(self, line):
        if len(line) > 0:
            cmd, params = self.parseInput(line)
            #print "( cmd: %s, params: %s )" % (cmd, params)
            success = self.validateCommand(cmd, params)
            if success:
                MobiApp.control.handleCommand(cmd, params)
        self.transport.write(">>> ")

    def parseInput(self, line):
        list = line.strip().split(' ')
        cmd = list[0]
        params = list[1:]
        return cmd, params

    def para_j(self,para,num):     #params judge
        if (len(para) == num) and ('' not in para):
            return True
        else:
            return False

    def validateCommand(self, cmd, params):
        if cmd not in self.commands_help.keys():
            self.sendLine("Unknown command: " + cmd)
            return False
        else:
            if (cmd == "request_authcode" and self.para_j(params,2)==False ) or \
                (cmd == "login_by_authcode" and self.para_j(params,2)==False ) or \
                (cmd == "login" and self.para_j(params,2)==False ) or \
                (cmd == "register_auth" and self.para_j(params,1)==False) or \
                (cmd == "register" and self.para_j(params,2)==False) or \
                (cmd == "change_password" and self.para_j(params,1)==False) or \
                (cmd == "reset_password" and self.para_j(params,3)==False) or \
                (cmd == "add_device" and self.para_j(params,1)==False) or \
                (cmd == "del_device" and self.para_j(params,1)==False) or \
                (cmd == "modify_device_alias" and self.para_j(params,2)==False) or \
                (cmd == "set_default_device" and self.para_j(params,1)==False) or \
                (cmd == "get_device_info" and self.para_j(params,1)==False) or \
                (cmd == "get_device_status" and self.para_j(params,1)==False) or \
                (cmd == "get_device_wlan_info" and self.para_j(params,1)==False) or \
                (cmd == "get_device_sn" and self.para_j(params,1)==False) or \
                (cmd == "device_charge" and self.para_j(params,1)==False) or \
                (cmd == "device_area_clean" and self.para_j(params,1)==False) or \
                (cmd == "device_auto_clean" and self.para_j(params,1)==False) or \
                (cmd == "device_manual_ctrl" and self.para_j(params,1)==False) or \
                (cmd == "device_navigate_move" and self.para_j(params,1)==False) or \
                (cmd == "device_point_clean" and self.para_j(params,1)==False) or \
                (cmd == "device_config_reset" and self.para_j(params,1)==False) or \
                (cmd == "device_wifi_ctrl" and self.para_j(params,1)==False) or \
                (cmd == "get_order_list" and self.para_j(params,1)==False) or \
                (cmd == "set_order_list" and self.para_j(params,1)==False) or \
                (cmd == "get_vwall_list" and self.para_j(params,1)==False) or \
                (cmd == "set_vwall_list" and self.para_j(params,1)==False) or \
                (cmd == "get_area_clean_info" and self.para_j(params,1)==False) or \
                (cmd == "map_ctrl" and self.para_j(params,2)==False) or \
                (cmd == "map_lidar_ctrl" and self.para_j(params,1)==False) or \
                (cmd == "device_upgrade_ctrl" and self.para_j(params,1)==False) or \
                (cmd == "device_control_lock" and self.para_j(params,1)==False) or \
                (cmd == "query_clean_info" and self.para_j(params,3)==False) or \
                (cmd == "query_clean_map" and self.para_j(params,2)==False) or \
                (cmd == "query_key_event" and self.para_j(params,3)==False) or \
                (cmd == "query_fault_event" and self.para_j(params,3)==False) :
                self.showHelp([cmd])
                return False
        return True

    def showHelp(self, params):
        if len(params) == 0:
            self.sendLine(self.help)
        else:
            cmd = params[0]
            if cmd in self.commands_help.keys():
                self.sendLine("Usage: " + self.commands_help[cmd])
            else:
                self.sendLine("Unknown command: " + cmd)

def parse_args():
    usage = """usage: %prog [options] [hostname]:port"""

    parser = optparse.OptionParser(usage)

    help = "The device id of MobiApp"
    parser.add_option('--cid', help=help, default=0)

    global g_options
    g_options, args = parser.parse_args()
    print "options: ", g_options

    if len(args) != 1:
        parser.error('Provide exactly one server address.')

    def parse_address(addr):
        if ':' not in addr:
            host = '0.0.0.0'
            port = addr
        else:
            host, port = addr.split(':', 1)

        if not port.isdigit():
            parser.error('Ports must be integers.')

        return host, int(port)

    return parse_address(args[0])

def signal_handler(signal, frame):
    print 'Terminating...'
    reactor.removeAll()
    reactor.stop()

def shutdown():
    print 'Terminating...'

def main():
    server_addr = parse_args()
    local_host, local_port = server_addr

    MobiApp.service = MobiAppService()
    MobiApp.cui = CUI()
    MobiApp.control = Control()
    stdio.StandardIO(MobiApp.cui)
    protocol_factory = MobiAppProtocolFactory()

    MobiApp.connector = reactor.connectTCP(local_host, local_port, protocol_factory)
    print 'MobiApp started, connect to %s:%d.' % server_addr

    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    #signal.signal(signal.SIGINT, signal_handler)
    reactor.run()


if __name__ == '__main__':
    main()
