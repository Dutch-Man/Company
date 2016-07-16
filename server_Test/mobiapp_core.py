#coding:utf-8
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#
import time
import datetime

from twisted.internet.protocol import ReconnectingClientFactory, Protocol
from twisted.internet import reactor
from twisted.internet import task

from message_base import *
from RsRobot_enum_pb2 import *
from RsRobot_pb2 import *
import gen_uid
from mobiapp_controller import *

class MobiAppMatrix:
    mobiapp_factory = None


class MobiAppProtocol(Protocol):
    def __init__(self):
        self.mq = MQ()
        self.mobiapp = MobiAppMatrix.mobiapp_factory.takeout_scheduling_mobiapp()
        self.mobiapp.init(self)
        if self.mobiapp is None:
            msg = "ERROR [MobiAppProtocol] Attach protocol to MobiApp failed, has no mobiapp in schedule queue."
            print msg
            self.output(msg)
        else:
            msg = "INFO [MobiAppProtocol] Attach protocol to MobiApp %s successful." % self.mobiapp.get_username()
            print msg
            self.output(msg)

    def connectionMade(self):
        self.output("INFO: [connectionMade] peer: %s" % self.transport.getPeer())
        self.transport.setTcpKeepAlive(1)
        self.mobiapp.start()

    def dataReceived(self, data):
        self.output("INFO: [dataReceived] Received bytes: %d" % len(data))
        self.mq.AppendData(data)
        self.mq.Apply(self.handle_message)

    def connectionLost(self, reason):
        self.output("INFO: [connectionLost] Connection lost: %s" % reason.getErrorMessage())
        self.mobiapp.stop()
        MobiAppMatrix.mobiapp_factory.recycle_stopped_mobiapp(self.mobiapp)

    def closeConnection(self):
        self.transport.loseConnection()

    def handle_message(self, msg):
        self.output("Handle message: %s" % msg.Header())
        self.mobiapp.handle_message(msg)

    def send_message(self, hdr, msg):
        msg_data = ""
        if msg is not None:
            msg_data = msg.SerializeToString()
        hdr.length = hdr.LENGTH + len(msg_data)
        hdr_data = hdr.pack()
        self.output("Send message: %s" % hdr)
        self.transport.write(hdr_data)
        if len(msg_data) > 0:
            self.transport.write(msg_data)

    def output(self, msg):
        if self.mobiapp:
            self.mobiapp.output(msg)
        else:
            print msg

class MobiAppProtocolFactory(ReconnectingClientFactory):
    protocol = MobiAppProtocol

    def __init__(self, mobiapp_factory):
        self.mobiapp_factory = mobiapp_factory

    def clientConnectionFailed(self, connector, reason):
        msg = "ERROR: [clientConnectionLost] Connection failed: %s" % reason.getErrorMessage()
        print msg
        self.mobiapp_factory.output('###########', msg)
        mobiapp = self.mobiapp_factory.takeout_scheduling_mobiapp()
        mobiapp.stop()
        self.mobiapp_factory.recycle_stopped_mobiapp(mobiapp)

    def clientConnectionLost(self, connector, reason):
        #print "INFO: [clientConnectionLost] Connection lost: %s" % reason.getErrorMessage()
        pass

class MobiAppAutomation(object):
    def __init__(self, mobiapp):
        self.mobiapp = mobiapp
        class Operation:
            def __init__(self, cmd, params):
                self.cmd = cmd
                self.params = params
                self.in_progress = False
                self.time_tick = 0

            def dispatch(self, mobiapp):
                mobiapp.get_controller().handleCommand(self.cmd, self.params)
                self.in_progress = True
                self.time_tick = 1 

        self.operation_index = 0
        self.operation_list = []
        self.operation_list.append(Operation("register_auth", [self.mobiapp.username]))
        self.operation_list.append(Operation("register", [self.mobiapp.password, "x"]))
        self.operation_list.append(Operation("login", [self.mobiapp.username, self.mobiapp.password]))


    def run(self):
        if self.operation_index < len(self.operation_list):
            operation = self.operation_list[self.operation_index]
            if not operation.in_progress:
                operation.dispatch(self.mobiapp)
            elif operation.time_tick > 3:
                self.mobiapp.output("Automation operation (%s) timeout" % operation.cmd)
                self.operation_finish()
            else:
                operation.time_tick += 1
        else:
            self.mobiapp.stop_automation()

    def operation_finish(self):
        operation = self.operation_list[self.operation_index]
        operation.in_progress = False
        self.operation_index += 1

    def get_next_operation(self):
        pass

class MobiApp(object):
    def __init__(self, factory, username, password):
        self.factory = factory
        self.ctype = MOBIAPP
        self.controller = MobiAppController(self)
        self.protocol = None
        self.interactive_mode = False

        self.username = username
        self.password = password
        self.sessionid = ""
        self.uid = 0;
        self.devinfo_list = [] 

        self.uid_gen = gen_uid.UIDGenerator()

        self.timer_periodic = 60  # seconds
        self.heartbeat_timer = task.LoopingCall(self.heartbeat_sender)


        self.enable_automation = False
        self.automation = MobiAppAutomation(self)
        self.automation_periodic = 10
        self.automation_timer = task.LoopingCall(self.automation.run)

        self.returned_authcode = ""

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

    def show_info(self):
        print "connected: ", "true" if self.protocol else "false"
        print "username: ", self.username
        print "password: ", self.password
        print "sessionid: ", self.sessionid
        print "uid: ", self.uid
        print "heartbeat timer periodic: %d, status: %s" % (self.timer_periodic, "running" if self.heartbeat_timer.running else "stopped")
        print "devinfo list: "
        for devinfo in self.devinfo_list:
            print devinfo

    def get_controller(self):
        return self.controller

    def get_username(self):
        return self.username

    def set_interactive_mode(self, interactive):
        self.interactive_mode = interactive

    def output(self, msg):
        if self.interactive_mode == True:
            print msg
        else:
            self.factory.output(self.username, msg)

    def init(self, protocol):
        self.protocol = protocol
        self.output("-" * 50)
        self.output("MobiApp %s start" % self.username)

    def start(self):
        self.send_online_request()
        self.enable_heartbeat()
        if self.enable_automation and not self.automation_timer.running:
            self.automation_timer.start(self.automation_periodic)
        self.timer_start()

    def stop(self):
        if self.protocol:
            self.protocol.closeConnection()
            self.protocol = None
            self.timer_stop()
        self.disable_heartbeat()
        if self.automation_timer.running:
            self.automation_timer.stop()
        self.output("MobiApp stopped")

    def timer_start(self):
        #self.output("Start timer")
        #self.periodic_timer.start(self.timer_periodic);  # seconds
        pass

    def timer_stop(self):
        #if self.periodic_timer.running:
        #    self.periodic_timer.stop()
        #    self.output("Stop timer")
        pass

    def set_automation(self, enable):
        self.enable_automation = enable

    def start_automation(self):
        self.enable_automation = True
        if not self.automation_timer.running:
            self.automation_timer.start(self.automation_periodic)
        self.output("Automation started")

    def stop_automation(self):
        if self.automation_timer.running:
            self.automation_timer.stop()
            self.enable_automation = False
            self.output("Automation stopped")

    def heartbeat_sender(self):
        self.send_heartbeat_request()

    def enable_heartbeat(self):
        self.output("heartbeat enabled")
        if not self.heartbeat_timer.running:
            self.heartbeat_timer.start(self.timer_periodic);

    def disable_heartbeat(self):
        if self.heartbeat_timer.running:
            self.heartbeat_timer.stop()
        self.output("heartbeat disabled")

    def send_message(self, hdr, body, req_desc):
        if self.protocol:
            self.protocol.send_message(hdr, body)
            self.output("Sent %s request, seq no: %x" % (req_desc, hdr.seq))
            return True
        else:
            self.output("Connection not available, please connect first")
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
            self.output("Unknown biz_type: %s" % biz_type)
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
        body.authcode = authcode if authcode != "x" else self.returned_authcode
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
        body.authcode = authcode if authcode != "x" else self.returned_authcode
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
        body.authcode = authcode if authcode != "x" else self.returned_authcode
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
            if self.enable_automation:
                self.automation.operation_finish()
        elif msg.Header().cmd == USER_LOGOUT_RSP:
            self.handle_user_logout_response(msg)
        elif msg.Header().cmd == USER_REGISTER_AUTH_RSP:
            self.handle_user_register_auth_response(msg)
            if self.enable_automation:
                self.automation.operation_finish()
        elif msg.Header().cmd == USER_REGISTER_RSP:
            self.handle_user_register_response(msg)
            if self.enable_automation:
                self.automation.operation_finish()
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
            self.output("Unknown message: %s" % msg.Header())


    def handle_user_request_authcode_response(self, msg):
        self.output("[UserRequestAuthCodeResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0 and rsp.errstr:
            self.returned_authcode = rsp.errstr
        self.output(rsp)

    def handle_user_login_by_authcode_response(self, msg):
        self.output("[UserLoginByAuthCodeResponse]")
        self.handle_user_login_response(msg)

    def handle_reset_password_response(self, msg):
        self.output("[UserResetPasswordResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_user_login_response(self, msg):
        self.output("[UserLoginResponse]")
        rsp = UserLoginResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.uid = rsp.attrs.uid
            self.sessionid = rsp.attrs.sessionid
        self.output(rsp)

    def handle_user_logout_response(self, msg):
        self.output("[UserLogoutResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.sessionid = ""
            self.uid = 0
            self.devinfo_list = []
        self.output(rsp)

    def handle_user_register_auth_response(self, msg):
        self.output("[UserRegisterAuthResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0 and rsp.errstr:
            self.returned_authcode = rsp.errstr
        self.output(rsp)

    def handle_user_register_response(self, msg):
        self.output("[UserRegisterResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_client_online_response(self, msg):
        self.output("[MobiAppOnlineResponse]")
        self.output("  Empty Params")

    def handle_client_heartbeat_response(self, msg):
        self.output("[MobiAppHeartbeatResponse]")
        self.output("  Empty Params")

    def handle_change_password_response(self, msg):
        self.output("[UserChangePasswordResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_modify_profile_response(self, msg):
        self.output("[UserModifyProfileResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_get_profile_response(self, msg):
        self.output("[UserGetProfileResponse]")
        rsp = UserGetProfileResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.output("  User get profile SUCCESS")
            self.output("  { nickname: %s, sex: %s, age: %d, job: %s }" % (rsp.profile.nickname, "male" if rsp.profile.sex == 1 else "female", rsp.profile.age, rsp.profile.job))
        else:
            self.output("  error code: %s" % rsp.errcode)
            self.output("  error str: %s" % rsp.errstr)

    def handle_add_device_response(self, msg):
        self.output("[UserAddDeviceResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_del_device_response(self, msg):
        self.output("[UserDeleteDeviceResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_get_device_list_response(self, msg):
        self.output("[UserGetDeviceListResponse]")
        rsp = UserGetDeviceListResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.devinfo_list = []
            if len(rsp.attrs.udi_list) == 0:
                self.output("No devices")
            else:
                for devinfo in rsp.attrs.udi_list:
                    devinfo_str = " { devsn: %s, devid: %d, ctime: %d, status: %d, alias: %s, is_default: %s }" % \
                            (devinfo.devsn, devinfo.devid, devinfo.ctime, devinfo.status, devinfo.alias if devinfo.alias else "", "true" if devinfo.is_default else "false")
                    self.output(devinfo_str)
                    self.devinfo_list.append(devinfo_str)
        else:
            self.output("  error code: %s" % rsp.errcode)
            self.output("  error str: %s" % rsp.errstr)

    def handle_modify_device_alias_response(self, msg):
        self.output("[UserModifyDeviceAliasResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_change_default_device_response(self, msg):
        self.output("[UserChangeDefaultDeviceResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_get_device_info_response(self, msg):
        self.output("[UserGetDeviceInfoResponse]")
        rsp = DeviceInfoGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_get_device_status_response(self, msg):
        self.output("[UserGetDeviceStatusResponse]")
        rsp = DeviceStatusGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_get_device_wlan_info_response(self, msg):
        self.output("[UserGetDeviceWLANInfoResponse]")
        rsp = DeviceWLANInfoGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_get_device_sn_response(self, msg):
        self.output("[UserGetDeviceSNResponse]")
        rsp = DeviceSnGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_charge_response(self, msg):
        self.output("[DeviceChargeResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_areaclean_response(self, msg):
        self.output("[DeviceAreaCleanResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_autoclean_response(self, msg):
        self.output("[DeviceAutoCleanResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_manual_ctrl_response(self, msg):
        self.output("[DeviceManualCtrlResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_navigate_move_response(self, msg):
        self.output("[DeviceNavigateMoveResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_point_clean_response(self, msg):
        self.output("[DevicePointCleanResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_config_reset_response(self, msg):
        self.output("[DeviceConfigResetResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_wifi_ctrl_response(self, msg):
        self.output("[DeviceWifiCtrlResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_get_orderlist_response(self, msg):
        self.output("[DeviceCleanOrderListGettingResponse]")
        rsp = DeviceCleanOrderListGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_set_orderlist_response(self, msg):
        self.output("[DeviceCleanOrderListSettingResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_get_vwall_list_response(self, msg):
        self.output("[DeviceVWallListGettingResponse]")
        rsp = DeviceVirtualWallListGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_set_vwall_list_response(self, msg):
        self.output("[DeviceVWallListSettingResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_get_areaclean_info_response(self, msg):
        self.output("[DeviceAreaCleanInfoGettingResponse]")
        rsp = DeviceAreaCleanGettingResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_map_ctrl_response(self, msg):
        self.output("[DeviceMapCtrlResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_upgrade_ctrl_response(self, msg):
        self.output("[DeviceUpgradeCtrlResponse]")
        rsp = DeviceUpgradeCtrlResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_upgrade_package_info_response(self, msg):
        self.output("[DeviceUpgradePackageInfoResponse]")
        rsp = DeviceUpgradePackageInfo()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_upgrade_progress_info_response(self, msg):
        self.output("[DeviceUpgradeProgressInfoResponse]")
        rsp = DeviceUpgradeProgressInfo()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_device_control_lock_response(self, msg):
        self.output("[DeviceControlLockResponse]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_query_clean_info_response(self, msg):
        self.output("[QueryCleanInfoResponse]")
        rsp = QueryCleanInfoResult()
        rsp.ParseFromString(msg.Payload())
        cleaninfo_size = len(rsp.cleaninfo_list.cleaninfo)
        if cleaninfo_size < 20:
            self.output(rsp)
        else:
            self.output("NOTE: cleaninfo more than 20, only print the size: %d" % cleaninfo_size)

    def handle_query_clean_map_response(self, msg):
        self.output("[QueryCleanMapResponse]")
        rsp = QueryCleanMapResult()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_query_key_event_response(self, msg):
        self.output("[QueryKeyEventResponse]")
        rsp = QueryKeyEventResult()
        rsp.ParseFromString(msg.Payload())
        keyevent_size = len(rsp.keyevent_list.keyevent)
        if keyevent_size < 20:
            self.output(rsp)
        else:
            self.output("NOTE: keyevent more than 20, only print the size: %d" % keyevent_size)

    def handle_query_fault_event_response(self, msg):
        self.output("[QueryFaultEventResponse]")
        rsp = QueryFaultEventResult()
        rsp.ParseFromString(msg.Payload())
        faultevent_size = len(rsp.faultevent_list.faultevent)
        if faultevent_size < 20:
            self.output(rsp)
        else:
            self.output("NOTE: faultevent more than 20, only print the size: %d" % faultevent_size)

    def handle_user_kickout_cmd(self, msg):
        self.output("[UserKickoutCmd]")
        rsp = CommonResult()
        rsp.ParseFromString(msg.Payload())
        self.sessionid = ""
        self.devinfo_list = []
        self.output(rsp)

    def handle_fault_event_report(self, msg):
        self.output("[FaultEventReport]")
        rsp = DeviceFaultEventReportParams()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_key_event_report(self, msg):
        self.output("[KeyEventReport]")
        rsp = DeviceKeyEventReportParams()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_cleantask_event_report(self, msg):
        self.output("[CleanTaskEventReport]")
        rsp = DeviceCleanTaskReportParams()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)

    def handle_cleanmap_event_report(self, msg):
        self.output("[CleanMapEventReport]")
        rsp = DeviceMapReportParams()
        rsp.ParseFromString(msg.Payload())
        self.output(rsp)
