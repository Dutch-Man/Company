#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#

import optparse
import time
import datetime
import random

from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import ReconnectingClientFactory, Protocol
from twisted.internet import reactor
from twisted.internet import task

from message_base import *
from RsRobot_enum_pb2 import *
from RsRobot_pb2 import *
import gen_uid

g_options = None
g_sn_num = 1
def set_sn_start(n):
    global g_sn_num
    g_sn_num = n
class DeviceInfo:
    def __init__(self):
        self.softversion = "11.11"
        self.hardversion = "22.22"
        #self.devsn = "xxxx-yyyy-zzzz-00"
        self.mac = "00:11:22:33:44:55"
        self.battary_max = 90
        self.speed_max = 120
        self.angle_max = 60
        self.hz_max = 80
        self.modetype = 1

class DeviceStatus:
    def __init__(self):
        self.battary        = 60;
        self.charge_state   = 50;
        self.working_mode   = 1;
        self.area_clean_flag = 1;

class DeviceWLANInfo:
    def __init__(self):
        self.ipaddr  = "192.168.1.100";
        self.ssid    = "aaaaa-bbbbb-ccccc";
        self.port    = 9999;


class RobotProtocol(Protocol):
    def __init__(self):
        self.mq = MQ()
        global g_options
        if g_options.num ==1:
            sn =g_options.sn
        else:
            global g_sn_num
            sn = "xxxx-yyyy-" + "%d"%g_sn_num
            g_sn_num += 1
            p_file = open("./log/" + sn + ".log","w+")
            p_file.close()
        self.path = "./log/" + sn + ".log"
        self.service = RobotService(self,sn,self.path)
        self.sn = sn
    def connectionMade(self):
        string = "[connectionMade] peer: " + str(self.transport.getPeer())
        my_print(string,self.path)
        self.service.timer_start()
	print self.sn

    def dataReceived(self, data):
        string = "INFO: [dataReceived] Received bytes: %d" % len(data)
        my_print(string,self.path)
        self.mq.AppendData(data)
        self.mq.Apply(self.handle_message)

    def connectionLost(self, reason):
        string = "INFO: [connectionLost] Connection lost: %s" % reason.getErrorMessage()
        my_print(string,self.path)

        protocol_lost = open("./fault/%s.lost"%self.sn,"a+")
        protocol_lost.write(string)
        protocol_lost.close()

        self.transport.loseConnection()
#        Robot.protocol = None

    def handle_message(self, msg):
        string = "Handle message: " + str(msg.Header())
        my_print(string,self.path)
        self.service.handle_message(msg)

    def send_response(self, hdr, rsp):
        self.send_message(hdr, rsp)

    def send_message(self, hdr, msg):
        msg_data = ""
        if msg is not None:
            msg_data = msg.SerializeToString()
        hdr.length = hdr.LENGTH + len(msg_data)
        hdr_data = hdr.pack()
        string = "Send message: " + str(hdr)
        my_print(string,self.path)
        self.transport.write(hdr_data)
        if len(msg_data) > 0:
            self.transport.write(msg_data)


class RobotProtocolFactory(ReconnectingClientFactory):
    protocol = RobotProtocol

    def clientConnectionFailed(self, connector, reason):
        my_print("[RobotProtocolFactory] Make connection failed (%s): %s" % \
        (connector.getDestination(), reason), "./connection_failed.txt")

    def clientConnectionLost(self, connector, reason):
        my_print("[RobotProtocolFactory] Connection lost (%s): %s" % \
        (connector.getDestination(), reason), "./connection_lost.txt")

class RobotService(object):
    def __init__(self, protocol,sn,path):
        self.protocol = protocol
        self.time = int(time.time())
        self.ctype = DEVICE
        self.timer_periodic = 30
        self.last_time_sync = int(time.time())
        self.seq = 0
        self.uid_gen = gen_uid.UIDGenerator()

	if g_options.r == "True":
		self.device_registered = True
	else:
		self.device_registered = False
        #self.devsn = "xxxxxxx-yyyyyyy-zzzzzzzzzzz-" + str(g_options.cid)
        if g_options.num == 1:
		self.devsn = g_options.sn
	else:
		self.devsn = sn
	self.path = path
        self.devid = 0
        self.task_id = 0
        self.ctrl_uid = 0

        self.info = DeviceInfo()
        self.status = DeviceStatus()
        self.wlan = DeviceWLANInfo()

    def timer_start(self):
        self.periodic_timer = task.LoopingCall(self.timer_handler)
        self.periodic_timer.start(self.timer_periodic);  # seconds
        #print "Start timer"

    def timer_stop(self):
        if self.periodic_timer is not None:
            self.periodic_timer.stop()
            print "Stop timer"

    def get_next_seq(self):
        return self.uid_gen.get_uid()

    def get_next_taskid(self):
        self.task_id += 1
        return self.task_id

    def send_message(self, hdr, body, req_desc):
        if self.protocol:
            self.protocol.send_message(hdr, body)
	    string = "Sent %s message, seq no: %x" % (req_desc, hdr.seq)
	    my_print(string,self.path)
            return True
        else:
            string =  "Connection not available, please connect first"
	    my_print(string,self.path)
            return False

    def send_register_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_REGISTER_REQ
        body = DeviceRegisterParams()
        body.devsn = self.devsn
        body.softversion = "11.11"
        body.hardversion = "22.22"
        body.mac = "fc:aa:14:e5:f0:10"
        body.modetype = 1
        self.send_message(hdr, body, "register request")

    def send_online_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.seq = self.get_next_seq();
        hdr.cmd = CLIENT_ONLINE_REQ
        body = DeviceOnlineParams()
        body.devsn = self.devsn
        self.send_message(hdr, body, "device online request")

    def send_time_sync_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_TIME_SYNC_REQ
        self.send_message(hdr, None, "time sync request")

    def send_heartbeat_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.seq = self.get_next_seq();
        hdr.cmd = CLIENT_HEARTBEAT_REQ
        self.send_message(hdr, None, "heartbeat request")

    def send_keyevent_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = self.ctrl_uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_EVENT_REPORT_KEY
        body = DeviceKeyEventReportParams()
        body.type = 1;
        body.key_value = 11
        self.send_message(hdr, body, "key event request")

    def send_faultevent_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = self.ctrl_uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_EVENT_REPORT_FAULT
        body = DeviceFaultEventReportParams()
        body.fault_type = 1
        body.fault_code = 33
        self.send_message(hdr, body, "fault event request")

    def send_cleaninfo_event_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = self.ctrl_uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_EVENT_REPORT_CLEANTASK
        body = DeviceCleanTaskReportParams()
        body.task_id = self.task_id
        body.time_begin = int(time.time()) - 60 * 60
        body.time_end = int(time.time())
        body.total_area = random.randint(1,100)
        body.clean_rate = random.randint(1, 10) 
        body.clean_type = random.randint(1, 3)
        body.task_status = 0
        self.send_message(hdr, body, "clean info event request")

    def send_cleanmap_event_request(self):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = self.ctrl_uid
        hdr.seq = self.get_next_seq();
        hdr.cmd = DEVICE_EVENT_REPORT_CLEANMAP
        body = DeviceMapReportParams()
        body.task_id = self.task_id
        body.mapData = "xxxxx\0xxxxxxx"
        body.pathData = "\0yyyyyyyyyyyy"
        body.vwallData = "zzzzzz\0zzzzzz\0"
        self.send_message(hdr, body, "clean map event request")

    def timer_handler(self):
        if not self.device_registered:
            self.send_register_request()
        elif self.devid == 0:
            self.send_online_request()
        else:
            #return   # FIXME
            self.send_heartbeat_request()

            if int(time.time()) - self.last_time_sync > self.timer_periodic * 4:
                self.last_time_sync = int(time.time())
                self.send_time_sync_request()

            if int(time.time()) - self.last_time_sync > self.timer_periodic * 2:
                self.send_faultevent_request()
                self.send_keyevent_request()

                self.get_next_taskid()
                self.send_cleaninfo_event_request()
                self.send_cleanmap_event_request()

    def handle_message(self, msg):
        if msg.Header().cmd == DEVICE_TIME_SYNC_RSP:
            self.handle_device_time_sync_response(msg)
        elif msg.Header().cmd == DEVICE_REGISTER_RSP:
            self.handle_device_register_response(msg)
        elif msg.Header().cmd == CLIENT_ONLINE_RSP:
            self.handle_device_online_response(msg)
        elif msg.Header().cmd == CLIENT_HEARTBEAT_RSP:
            self.handle_device_heartbeat_response(msg)
        elif msg.Header().cmd == DEVICE_EVENT_REPORT_RSP:
            self.handle_device_cleanmap_report_response(msg)
        elif msg.Header().cmd == DEVICE_SN_GETTING_REQ:
            self.handle_device_sn_getting_request(msg)
        elif msg.Header().cmd == DEVICE_INFO_GETTING_REQ:
            self.handle_device_info_getting_request(msg)
        elif msg.Header().cmd == DEVICE_STATUS_GETTING_REQ:
            self.handle_device_status_getting_request(msg)
        elif msg.Header().cmd == DEVICE_WLAN_INFO_GETTING_REQ:
            self.handle_device_wlan_info_getting_request(msg)
        elif msg.Header().cmd == DEVICE_CHARGE_REQ:
            self.handle_device_charge_request(msg)
        elif msg.Header().cmd == DEVICE_AREA_CLEAN_REQ:
            self.handle_device_area_clean_request(msg)
        elif msg.Header().cmd == DEVICE_AUTO_CLEAN_REQ:
            self.handle_device_auto_clean_request(msg)
        elif msg.Header().cmd == DEVICE_MANUAL_CTRL_REQ:
            self.handle_device_manual_ctrl_request(msg)
        elif msg.Header().cmd == DEVICE_NAVIGATE_MOVE_REQ:
            self.handle_device_navigate_move_request(msg)
        elif msg.Header().cmd == DEVICE_POINT_CLEAN_REQ:
            self.handle_device_point_clean_request(msg)
        elif msg.Header().cmd == DEVICE_CONFIG_RESET_REQ:
            self.handle_device_config_reset_request(msg)
        elif msg.Header().cmd == DEVICE_WIFI_CTRL_REQ:
            self.handle_device_wifi_ctrl_request(msg)
        elif msg.Header().cmd == DEVICE_ORDERLIST_GETTING_REQ:
            self.handle_device_orderlist_getting_request(msg)
        elif msg.Header().cmd == DEVICE_ORDERLIST_SETTING_REQ:
            self.handle_device_orderlist_setting_request(msg)
        elif msg.Header().cmd == DEVICE_VWALL_LIST_GETTING_REQ:
            self.handle_device_vwall_list_getting_request(msg)
        elif msg.Header().cmd == DEVICE_VWALL_LIST_SETTING_REQ:
            self.handle_device_vwall_list_setting_request(msg)
        elif msg.Header().cmd == DEVICE_AREACLEAN_INFO_GETTING_REQ:
            self.handle_device_areaclean_info_getting_request(msg)
        elif msg.Header().cmd == DEVICE_MAP_CTRL_REQ:
            self.handle_device_map_ctrl_request(msg)
        elif msg.Header().cmd == DEVICE_MAP_LIDAR_CTRL_REQ:
            self.handle_device_lidar_ctrl_request(msg)
        elif msg.Header().cmd == DEVICE_UPGRADE_CTRL_REQ:
            self.handle_device_upgrade_ctrl_request(msg)
        elif msg.Header().cmd == DEVICE_CONTROL_LOCK_REQ:
            self.handle_device_control_lock_request(msg)
        elif msg.Header().cmd == COMMON_ERROR_REPLY:
            self.handle_common_error_reply(msg)
        else:
            string = "Unknown message, command: %d" % msg.Header().cmd
	    my_print(string,self.path)
            return

    def handle_device_time_sync_response(self, msg):
        string = "[DeviceTimeSyncResponse]"
	my_print(string,self.path)
        rsp = DeviceTimeSyncResult()
        rsp.ParseFromString(msg.Payload())
        string = str(rsp)
	my_print(string,self.path)

    def handle_device_register_response(self, msg):
        string = "[DeviceRegisterResponse]"
	my_print(string,self.path)
        rsp = DeviceRegisterResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.devid = rsp.attrs.devid
            self.device_registered = True
        string = str(rsp)
	my_print(string,self.path)
	

    def handle_device_online_response(self, msg):
        string = "[DeviceOnlineResponse]"
	my_print(string,self.path)
        rsp = DeviceOnlineResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.devid = rsp.attrs.devid
            self.time = rsp.attrs.servertime
	string = str(rsp)
	my_print(string,self.path)

    def handle_device_heartbeat_response(self, msg):
        string = "[DeviceHeartbeatResponse]"
	my_print(string,self.path)
        string =  "  Empty Params"
	my_print(string,self.path)

    def handle_device_cleanmap_report_response(self, msg):
        string = "[DeviceCleanMapReportResponse]"
	my_print(string,self.path)
        rsp = DeviceMapReportResult()
        rsp.ParseFromString(msg.Payload())
        string = str(rsp)
	my_print(string,self.path)

    def handle_device_sn_getting_request(self, msg):
        string = "[DeviceSnGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceSnGettingResult()
            req.ParseFromString(msg.Payload())
            string = " Request params: " + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_sn_response(msg.Header())
        self.send_message(hdr, rsp, "device sn getting response")

    def build_device_sn_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_SN_GETTING_RSP

        rsp = DeviceSnGettingResult()
        rsp.errcode = 0
        rsp.attrs.devsn = self.devsn
        rsp.attrs.devid = self.devid
        return hdr, rsp

    def build_device_info_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_INFO_GETTING_RSP

        rsp = DeviceInfoGettingResult()
        rsp.errcode = 0
        rsp.attrs.softversion = self.info.softversion
        rsp.attrs.hardversion = self.info.hardversion
        rsp.attrs.devsn = self.devsn
        rsp.attrs.mac = self.info.mac
        rsp.attrs.battary_max = self.info.battary_max
        rsp.attrs.speed_max = self.info.speed_max
        rsp.attrs.angle_max = self.info.angle_max
        rsp.attrs.hz_max = self.info.hz_max
        rsp.attrs.modetype = self.info.modetype

        return hdr, rsp

    def build_device_status_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_STATUS_GETTING_RSP

        rsp = DeviceStatusGettingResult()
        rsp.errcode = 0
        rsp.attrs.battary = self.status.battary
        rsp.attrs.charge_state = self.status.charge_state
        rsp.attrs.working_mode = self.status.working_mode
        rsp.attrs.area_clean_flag = self.status.area_clean_flag

        return hdr, rsp

    def build_device_wlan_info_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_WLAN_INFO_GETTING_RSP

        rsp = DeviceWLANInfoGettingResult()
        rsp.errcode = 0
        rsp.attrs.ipaddr = self.wlan.ipaddr
        rsp.attrs.ssid = self.wlan.ssid
        rsp.attrs.port = self.wlan.port

        return hdr, rsp

    def build_device_common_response(self, req_hdr, cmd, errcode = 0, errstr = None):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = cmd

        rsp = CommonResult()
        rsp.errcode = errcode
        if errstr:
            rsp.errstr = errstr

        return hdr, rsp

    def build_device_orderlist_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_ORDERLIST_GETTING_RSP

        rsp = DeviceCleanOrderListGettingResult()
        rsp.errcode = 0
        rsp.order.weekday_list.append(1)
        rsp.order.weekday_list.append(3)
        rsp.order.weekday_list.append(5)
        rsp.order.day_time = int(time.time())

        return hdr, rsp

    def build_device_vwall_list_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_VWALL_LIST_GETTING_RSP

        rsp = DeviceVWallListGettingResult()
        rsp.errcode = 0
        for i in range(1, 5):
            vw = VirtualWall()
            vw.enable = 1
            vw.start_x = i
            vw.start_y = i
            vw.end_x = i
            vw.end_y = i
            rsp.attrs.vwall_list.append(vw)

        return hdr, rsp

    def build_device_areaclean_info_getting_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_AREACLEAN_INFO_GETTING_RSP

        rsp = DeviceAreaCleanGettingResult()
        rsp.errcode = 0
        rsp.attrs.enable = 1
        rsp.attrs.area_num = 2
        rsp.attrs.areaid_list.append(1)
        rsp.attrs.areaid_list.append(2)

        return hdr, rsp

    def build_device_upgrade_ctrl_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_UPGRADE_CTRL_RSP

        rsp = DeviceUpgradeCtrlResult()
        rsp.errcode = 0
        rsp.attrs.cmd = 1
        rsp.attrs.value = 2

        return hdr, rsp

    def build_device_upgrade_package_info_response(self, req_hdr):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = req_hdr.cid
        hdr.seq = req_hdr.seq;
        hdr.cmd = DEVICE_UPGRADE_PACKAGE_INFO_RSP

        rsp = DeviceUpgradePackageInfo()
        rsp.newVersion = 11
        rsp.packageSize = "50M"
        rsp.systemVersion = "12"
        rsp.otaPackVersion = "13"
        rsp.remoteUrl = "http://localhost:8080/device_upgrade"

        return hdr, rsp

    def build_device_upgrade_progress_info_response(self, did, seq, upgrade_completion):
        hdr = MessageHeader()
        hdr.ctype = self.ctype
        hdr.cid = self.devid
        hdr.did = did
        hdr.seq = seq;
        hdr.cmd = DEVICE_UPGRADE_PROGRESS_INFO_RSP

        rsp = DeviceUpgradeProgressInfo()
        rsp.percent = upgrade_completion
        rsp.rate = "1.1"
        rsp.time = str(datetime.datetime.now())

        return hdr, rsp

    def handle_device_info_getting_request(self, msg):
        string = "[DeviceInfoGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceInfoGettingParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_info_response(msg.Header())
        self.send_message(hdr, rsp, "device info getting response")

    def handle_device_status_getting_request(self, msg):
        string = "[DeviceStatusGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceStatusGettingParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n", req
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,slef.path)

        hdr, rsp = self.build_device_status_response(msg.Header())
        self.send_message(hdr, rsp, "device status getting response")

    def handle_device_wlan_info_getting_request(self, msg):
        string = "[DeviceWlanInfoGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceWLANInfoGettingParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n", req
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_wlan_info_response(msg.Header())
        self.send_message(hdr, rsp, "device wlan info getting response")

    def handle_device_charge_request(self, msg):
        string = "[DeviceChargeRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceChargeParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_CHARGE_RSP)
        self.send_message(hdr, rsp, "device charge response")

    def handle_device_area_clean_request(self, msg):
        string = "[DeviceAreaCleanRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceAreaCleanParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_AREA_CLEAN_RSP)
        self.send_message(hdr, rsp, "device area clean response")

    def handle_device_auto_clean_request(self, msg):
        string = "[DeviceAutoCleanRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceAutoCleanParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_AUTO_CLEAN_RSP)
        self.send_message(hdr, rsp, "device auto clean response")

    def handle_device_manual_ctrl_request(self, msg):
        string = "[DeviceManualCtrlRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceManualCtrlParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MANUAL_CTRL_RSP)
        self.send_message(hdr, rsp, "device manual ctrl response")

    def handle_device_navigate_move_request(self, msg):
        string = "[DeviceNavigateMoveRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceNavigateMoveParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_NAVIGATE_MOVE_RSP)
        self.send_message(hdr, rsp, "device navigate move response")

    def handle_device_point_clean_request(self, msg):
        string = "[DevicePointCleanRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DevicePointCleanParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_POINT_CLEAN_RSP)
        self.send_message(hdr, rsp, "device point clean response")

    def handle_device_config_reset_request(self, msg):
        string = "[DeviceConfigResetRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceConfigResetParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_CONFIG_RESET_RSP)
        self.send_message(hdr, rsp, "device config reset response")

    def handle_device_wifi_ctrl_request(self, msg):
        string = "[DeviceWifiCtrlRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceWIFICtrlParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_WIFI_CTRL_RSP)
        self.send_message(hdr, rsp, "device wifi ctrl response")

    def handle_device_orderlist_getting_request(self, msg):
        string = "[DeviceOrderListGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceOrderListGettingParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_orderlist_response(msg.Header())
        self.send_message(hdr, rsp, "device order list getting response")

    def handle_device_orderlist_setting_request(self, msg):
        string = "[DeviceOrderListSettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = CleanOrderParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_ORDERLIST_SETTING_RSP)
        self.send_message(hdr, rsp, "device order list settting response")

    def handle_device_vwall_list_getting_request(self, msg):
        string = "[DeviceVWallListGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceVWallListGettingParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n", req
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_vwall_list_response(msg.Header())
        self.send_message(hdr, rsp, "device vwall list getting response")

    def handle_device_vwall_list_setting_request(self, msg):
        string = "[DeviceVWallListSettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceVirtualWallList()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_VWALL_LIST_SETTING_RSP)
        self.send_message(hdr, rsp, "device vwall list setting response")

    def handle_device_areaclean_info_getting_request(self, msg):
        string = "[DeviceAreaCleanGettingRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceAreaCleanParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_areaclean_info_getting_response(msg.Header())
        self.send_message(hdr, rsp, "device area clean getting response")

    def handle_device_map_ctrl_request(self, msg):
        string = "[DeviceMapCtrlRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceMapCtrlParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr = None
        rsp = None
        if req.map_type == 1:
            hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MAP_GLOBAL_DATA)
        elif req.map_type == 2:
            hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MAP_LIDAR_DATA)
        elif req.map_type == 3:
            hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MAP_PATH_DATA)
        elif req.map_type == 4:
            hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MAP_POSITION_DATA)
        else:
            string = "Unknown map type: " + str(req.map_type)
	    my_print(string,self.path)
            return
        self.send_message(hdr, rsp, "device map ctrl response")

    def handle_device_lidar_ctrl_request(self, msg):
        string = "[DeviceLidarCtrlRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceLidarCtrlParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" + str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MAP_LIDAR_DATA)
        self.send_message(hdr, rsp, "device lidar ctrl response")

    def handle_device_upgrade_ctrl_request(self, msg):
        string = "[DeviceUpgradeCtrlRequest]"
	my_print(string,self.path)
        if msg.PayloadSize() > 0:
            req = DeviceUpgradeCtrlParams()
            req.ParseFromString(msg.Payload())
            string = " Request params:\n" +str(req)
	    my_print(string,self.path)
        else:
            string = " Request params: None"
	    my_print(string,self.path)

        hdr, rsp = self.build_device_upgrade_ctrl_response(msg.Header())
        self.send_message(hdr, rsp, "device upgrade ctrl response")

        hdr, rsp = self.build_device_upgrade_package_info_response(msg.Header())
        self.send_message(hdr, rsp, "device upgrade package info")

        self.req_cid = msg.Header().cid
        self.req_seq = msg.Header().seq
        self.upgrade_completion = 0
        hdr, rsp = self.build_device_upgrade_progress_info_response(self.req_cid, self.req_seq, self.upgrade_completion)
        self.send_message(hdr, rsp, "device upgrade progress info")

        self.upgrade_progress_timer = task.LoopingCall(self.upgrade_progress_report_handler)
        self.upgrade_progress_timer.start(3)

    def upgrade_progress_report_handler(self):
        if self.upgrade_completion >= 100:
            self.upgrade_progress_timer.stop()
            self.upgrade_progress_timer = None
            string = "Device upgrade completion."
	    my_print(string,self.path)
        else:
            self.upgrade_completion += 10
            hdr, rsp = self.build_device_upgrade_progress_info_response(self.req_cid, self.req_seq, self.upgrade_completion)
            self.send_message(hdr, rsp, "device upgrade progress info")

    def handle_device_control_lock_request(self, msg):
        string = "[DeviceControlLockRequest]"
	my_print(string,self.path)
        string = " Request params: None"
	my_print(string,self.path)

        self.ctrl_uid = msg.Header().cid;
        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_CONTROL_LOCK_RSP)
        self.send_message(hdr, rsp, "device control lock response")

    def handle_common_error_reply(self, msg):
        print "[CommonErrorReply]"
        req = CommonResult()
        req.ParseFromString(msg.Payload())
        print " Request params:\n", req


def parse_args():
    usage = """usage: %prog [options] [hostname]:port"""

    parser = optparse.OptionParser(usage)

    help = "Register device"
    parser.add_option('-r', help=help, default="True")

    help = "The device id of Robot"
    parser.add_option('--cid', help=help, default=0)

    help = "The device serial number of Robot"
    parser.add_option('--sn', help=help, default=0)

    help = "Number of device"
    parser.add_option('--num', help=help, default=1)

    help = "Start number of device"
    parser.add_option('--start', help=help, type = "int",default=0)

    help = "End number of device"
    parser.add_option('--end', help=help, type = "int",default=0)

    global g_options
    g_options, args = parser.parse_args()
    print "options: ", g_options
    global g_sn_num
    if g_options.start != 0:
        g_sn_num = g_options.start
    if g_options.end != 0:
        g_options.num = g_options.end - g_options.start + 1

    if len(args) != 1:
        parser.error('Provide exactly one server address.')
    if g_options.num == 1 and g_options.sn == 0:
        parser.error('Please provide device serial number with --sn.')
	
    def parse_address(addr):
        if ':' not in addr:
            host = '0.0.0.0'
            port = addr
        else:
            host, port = addr.split(':', 1)

        if not port.isdigit():
            parser.error('Ports must be integers.')

        return host, int(port)

    return parse_address(args[0]),g_options.num

def signal_handler(signal, frame):
    print 'Terminating...'
    reactor.removeAll()
    reactor.stop()

def my_print(string,path):
    global g_options
#    print "type(num) =",type(g_options.num)
#    print g_options.num
    if g_options.num == 1:
	print string
    else:
	#python write file
	p_file = open(path,"a")
	p_file.write(string+"\n")
	p_file.close()
def main():
    server_addr,num = parse_args()
    local_host, local_port = server_addr

    factory = RobotProtocolFactory()

    reactor.connectTCP(local_host, local_port, factory)
    print 'Robot started, connect to %s:%d.' % server_addr

    #signal.signal(signal.SIGINT, signal_handler)
    reactor.run()


if __name__ == '__main__':
    main()
