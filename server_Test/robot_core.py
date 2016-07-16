# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#
import time
import datetime
import random
import sys

from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory, Protocol
from twisted.internet import task

from message_base import *
from RsRobot_enum_pb2 import *
from RsRobot_pb2 import *
import gen_uid
from robot_factory import *


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

class RobotMatrix:
    robot_factory = None


class RobotProtocol(Protocol):
    def __init__(self):
        self.mq = MQ()
        self.robot = RobotMatrix.robot_factory.takeout_scheduling_robot()
        self.robot.init(self)
        if self.robot is None:
            msg = "ERROR [RobotProtocol] Attach protocol to Robot failed, has no robot in schedule queue."
            print msg
            self.log(msg)
        else:
            msg = "INFO [RobotProtocol] Attach protocol to Robot %s successful." % self.robot.get_devsn()
            print msg
            self.log(msg)

    def connectionMade(self):
        self.log("INFO [connectionMade] Peer: %s" % self.transport.getPeer())
        self.robot.start()

    def dataReceived(self, data):
        self.log("INFO [dataReceived] Received bytes: %d" % len(data))
        self.mq.AppendData(data)
        self.mq.Apply(self.handle_message)

    def connectionLost(self, reason):
        self.log("WARN [connectionLost] Connection lost: %s" % reason.getErrorMessage())
        self.robot.stop()
        RobotMatrix.robot_factory.recycle_stopped_robot(self.robot)

    def closeConnection(self):
        self.transport.loseConnection()

    def handle_message(self, msg):
        self.log("Handle message: %s" % msg.Header())
        self.robot.handle_message(msg)

    def send_message(self, hdr, msg):
        msg_data = ""
        if msg:
            msg_data = msg.SerializeToString()
        hdr.length = hdr.LENGTH + len(msg_data)
        hdr_data = hdr.pack()
        self.log("Send message: %s" % hdr)
        self.transport.write(hdr_data)
        if len(msg_data) > 0:
            self.transport.write(msg_data)

    def log(self, msg):
        if self.robot:
            self.robot.log(msg)
        else:
            print msg

class RobotProtocolFactory(ReconnectingClientFactory):
    protocol = RobotProtocol

    def __init__(self, robot_factory):
        self.robot_factory = robot_factory

    def clientConnectionFailed(self, connector, reason):
        msg = "ERROR: [clientConnectionLost] Connection failed: %s" % reason.getErrorMessage()
        print msg
        self.robot_factory.log('###########', msg)
        robot = self.robot_factory.takeout_scheduling_robot()
        robot.stop()
        self.robot_factory.recycle_stopped_robot(robot)

    def clientConnectionLost(self, connector, reason):
        #print "INFO: [clientConnectionLost] Connection lost: %s" % reason.getErrorMessage()
        pass

class Robot(object):
    def __init__(self, factory, devsn, registered):
        self.factory = factory
        self.server_time = 0
        self.ctype = DEVICE
        self.timer_periodic = 60
        self.last_time_sync = int(time.time())

        self.protocol = None
        self.devsn = devsn 
        self.registered = registered

        self.devid = 0
        self.task_id = 0
        self.ctrl_uid = 0

        self.uid_gen = gen_uid.UIDGenerator()
        self.periodic_timer = task.LoopingCall(self.timer_handler)

        self.info = DeviceInfo()
        self.status = DeviceStatus()
        self.wlan = DeviceWLANInfo()

    def show_info(self):
        print "devsn: %s" % self.devsn
        print "devid: %d" % self.devid
        print "connecting: %s" % "yes" if self.protocol else "no"

    def log(self, msg):
        self.factory.log(self.devsn, msg)

    def get_devsn(self):
        return self.devsn

    def get_devid(self):
        return self.devid

    def init(self, protocol):
        self.protocol = protocol
        self.log("-" * 50)
        self.log("Robot %s start" % self.devsn)

    def start(self):
        self.timer_start()

    def stop(self):
        if self.protocol:
            self.protocol.closeConnection()
            self.protocol = None
            self.timer_stop()
        self.log("Robot stopped")

    def timer_start(self):
        self.log("Start timer")
        if not self.periodic_timer.running:
            self.periodic_timer.start(self.timer_periodic);  # seconds

    def timer_stop(self):
        if self.periodic_timer.running:
            self.periodic_timer.stop()
        self.log("Stop timer")

    def timer_handler(self):
        if not self.registered:
            self.send_register_request()
        elif self.devid == 0:
            self.send_online_request()
        else:
            self.send_heartbeat_request()

            return   # FIXME
            now_ts = int(time.time())
            if now_ts - self.last_time_sync > self.timer_periodic * 4:
                self.last_time_sync = now_ts
                self.send_time_sync_request()

            if now_ts - self.last_time_sync > self.timer_periodic * 2:
                self.send_faultevent_request()
                self.send_keyevent_request()

                self.get_next_taskid()
                self.send_cleaninfo_event_request()
                self.send_cleanmap_event_request()

    def get_next_seq(self):
        return self.uid_gen.get_uid()

    def get_next_taskid(self):
        self.task_id += 1
        return self.task_id

    def send_message(self, hdr, body, req_desc):
        if self.protocol:
            self.protocol.send_message(hdr, body)
            self.log("Sent %s message, seq no: %x" % (req_desc, hdr.seq))
            return True
        else:
            self.log("Connection not available, please connect first")
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
            self.log("Unknown message, command: %d" % msg.Header().cmd)
            return

    def handle_device_time_sync_response(self, msg):
        self.log("[DeviceTimeSyncResponse]")
        rsp = DeviceTimeSyncResult()
        rsp.ParseFromString(msg.Payload())
        self.log(rsp)

    def handle_device_register_response(self, msg):
        self.log("[DeviceRegisterResponse]")
        rsp = DeviceRegisterResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.devid = rsp.attrs.devid
            self.registered = True
        self.log(rsp)

    def handle_device_online_response(self, msg):
        self.log("[DeviceOnlineResponse]")
        rsp = DeviceOnlineResult()
        rsp.ParseFromString(msg.Payload())
        if rsp.errcode == 0:
            self.devid = rsp.attrs.devid
            self.server_time = rsp.attrs.servertime
        elif rsp.errcode == 1:
            self.registered = False
        self.log(rsp)

    def handle_device_heartbeat_response(self, msg):
        self.log("[DeviceHeartbeatResponse]")
        self.log("  Empty Params")

    def handle_device_cleanmap_report_response(self, msg):
        self.log("[DeviceCleanMapReportResponse]")
        rsp = DeviceMapReportResult()
        rsp.ParseFromString(msg.Payload())
        self.log(rsp)

    def handle_device_sn_getting_request(self, msg):
        self.log("[DeviceSnGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceSnGettingResult()
            req.ParseFromString(msg.Payload())
            self.log(" Request params: %s" % req)
        else:
            self.log(" Request params: None")

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
        self.log("[DeviceInfoGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceInfoGettingParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_info_response(msg.Header())
        self.send_message(hdr, rsp, "device info getting response")

    def handle_device_status_getting_request(self, msg):
        self.log("[DeviceStatusGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceStatusGettingParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_status_response(msg.Header())
        self.send_message(hdr, rsp, "device status getting response")

    def handle_device_wlan_info_getting_request(self, msg):
        self.log("[DeviceWlanInfoGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceWLANInfoGettingParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_wlan_info_response(msg.Header())
        self.send_message(hdr, rsp, "device wlan info getting response")

    def handle_device_charge_request(self, msg):
        self.log("[DeviceChargeRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceChargeParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_CHARGE_RSP)
        self.send_message(hdr, rsp, "device charge response")

    def handle_device_area_clean_request(self, msg):
        self.log("[DeviceAreaCleanRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceAreaCleanParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_AREA_CLEAN_RSP)
        self.send_message(hdr, rsp, "device area clean response")

    def handle_device_auto_clean_request(self, msg):
        self.log("[DeviceAutoCleanRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceAutoCleanParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_AUTO_CLEAN_RSP)
        self.send_message(hdr, rsp, "device auto clean response")

    def handle_device_manual_ctrl_request(self, msg):
        self.log("[DeviceManualCtrlRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceManualCtrlParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MANUAL_CTRL_RSP)
        self.send_message(hdr, rsp, "device manual ctrl response")

    def handle_device_navigate_move_request(self, msg):
        self.log("[DeviceNavigateMoveRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceNavigateMoveParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_NAVIGATE_MOVE_RSP)
        self.send_message(hdr, rsp, "device navigate move response")

    def handle_device_point_clean_request(self, msg):
        self.log("[DevicePointCleanRequest]")
        if msg.PayloadSize() > 0:
            req = DevicePointCleanParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_POINT_CLEAN_RSP)
        self.send_message(hdr, rsp, "device point clean response")

    def handle_device_config_reset_request(self, msg):
        self.log("[DeviceConfigResetRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceConfigResetParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_CONFIG_RESET_RSP)
        self.send_message(hdr, rsp, "device config reset response")

    def handle_device_wifi_ctrl_request(self, msg):
        self.log("[DeviceWifiCtrlRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceWIFICtrlParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_WIFI_CTRL_RSP)
        self.send_message(hdr, rsp, "device wifi ctrl response")

    def handle_device_orderlist_getting_request(self, msg):
        self.log("[DeviceOrderListGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceOrderListGettingParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_orderlist_response(msg.Header())
        self.send_message(hdr, rsp, "device order list getting response")

    def handle_device_orderlist_setting_request(self, msg):
        self.log("[DeviceOrderListSettingRequest]")
        if msg.PayloadSize() > 0:
            req = CleanOrderParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_ORDERLIST_SETTING_RSP)
        self.send_message(hdr, rsp, "device order list settting response")

    def handle_device_vwall_list_getting_request(self, msg):
        self.log("[DeviceVWallListGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceVWallListGettingParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_vwall_list_response(msg.Header())
        self.send_message(hdr, rsp, "device vwall list getting response")

    def handle_device_vwall_list_setting_request(self, msg):
        self.log("[DeviceVWallListSettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceVirtualWallList()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_VWALL_LIST_SETTING_RSP)
        self.send_message(hdr, rsp, "device vwall list setting response")

    def handle_device_areaclean_info_getting_request(self, msg):
        self.log("[DeviceAreaCleanGettingRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceAreaCleanParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_areaclean_info_getting_response(msg.Header())
        self.send_message(hdr, rsp, "device area clean getting response")

    def handle_device_map_ctrl_request(self, msg):
        self.log("[DeviceMapCtrlRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceMapCtrlParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

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
            self.log("Unknown map type: %" % req.map_type)
            return
        self.send_message(hdr, rsp, "device map ctrl response")

    def handle_device_lidar_ctrl_request(self, msg):
        self.log("[DeviceLidarCtrlRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceLidarCtrlParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_MAP_LIDAR_DATA)
        self.send_message(hdr, rsp, "device lidar ctrl response")

    def handle_device_upgrade_ctrl_request(self, msg):
        self.log("[DeviceUpgradeCtrlRequest]")
        if msg.PayloadSize() > 0:
            req = DeviceUpgradeCtrlParams()
            req.ParseFromString(msg.Payload())
            self.log(" Request params:\n%s" % req)
        else:
            self.log(" Request params: None")

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
            self.log("Device upgrade completion.")
        else:
            self.upgrade_completion += 10
            hdr, rsp = self.build_device_upgrade_progress_info_response(self.req_cid, self.req_seq, self.upgrade_completion)
            self.send_message(hdr, rsp, "device upgrade progress info")

    def handle_device_control_lock_request(self, msg):
        self.log("[DeviceControlLockRequest]")
        self.log(" Request params: None")

        self.ctrl_uid = msg.Header().cid;
        hdr, rsp = self.build_device_common_response(msg.Header(), DEVICE_CONTROL_LOCK_RSP)
        self.send_message(hdr, rsp, "device control lock response")

    def handle_common_error_reply(self, msg):
        self.log("[CommonErrorReply]")
        req = CommonResult()
        req.ParseFromString(msg.Payload())
        self.log(" Request params: \n%s" % req)
