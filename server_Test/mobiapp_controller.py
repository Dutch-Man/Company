#coding:utf-8
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#
from mobiapp_core import *

commands_help = \
        { \
        '?'                       : '? [COMMAND]', \
        'help'                    : 'help [COMMAND]', \
        'enable_heartbeat'        : 'enable_heartbeat', \
        'disable_heartbeat'       : 'disable_heartbeat', \
        'automation'              : 'automation', \
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
  enable_heartbeat       : %s\n\
  disable_heartbeat      : %s\n\
  automation             : %s\n\
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
  commands_help['enable_heartbeat'],\
  commands_help['disable_heartbeat'],\
  commands_help['automation'],\
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

class MobiAppController:
    def __init__(self, mobiapp):
        self.mobiapp = mobiapp
        self.ui = None

    def set_ui(self, ui):
        self.ui = ui

    def handleCommand(self, cmd, params):
        success = self.validateCommand(cmd, params)
        if success:
            self.run(cmd, params)

    def run(self, cmd, params):
        if cmd in ["help", "?"]:
            self.showHelp(params)
        elif cmd == "enable_heartbeat":
            self.mobiapp.enable_heartbeat()
        elif cmd == "disable_heartbeat":
            self.mobiapp.disable_heartbeat()
        elif cmd == "automation":
            self.mobiapp.start_automation()
        elif cmd == "client_online":
            self.mobiapp.send_online_request()
        elif cmd == "status":
            self.mobiapp.show_info()
        elif cmd == "request_authcode":
            username = params[0]
            biz_type = params[1]
            self.mobiapp.send_request_authcode_request(username, biz_type)
        elif cmd == "login_by_authcode":
            username = params[0]
            authcode = params[1]
            self.mobiapp.send_login_by_authcode_request(username, authcode)
        elif cmd == "login":
            username = params[0]
            password = params[1]
            self.mobiapp.send_login_request(username, password)
        elif cmd == "logout":
            if len(self.mobiapp.sessionid) == 0:
                print "You are not login"
            else:
                self.mobiapp.send_logout_request()
        elif cmd == "register_auth":
            if len(self.mobiapp.sessionid) > 0:
                print "You are logged in, please logout first for user registration"
            else:
                username = params[0]
                self.mobiapp.send_register_auth_request(username)
        elif cmd == "register":
            print "username: ", self.mobiapp.username
            username = self.mobiapp.username
            password = params[0]
            authcode = params[1]
            self.mobiapp.send_register_request(username, password, authcode)
        elif cmd == "change_password":
            if self.mobiapp.password is None:
                print "Please login first"
            else:
                new_password = params[0]
                self.mobiapp.send_change_password_request(new_password)
        elif cmd == "reset_password":
            username = params[0]
            authcode = params[1]
            new_password = params[2]
            self.mobiapp.send_reset_password_request(username, authcode, new_password)
        elif cmd == "modify_profile":
            self.mobiapp.send_modify_profile_request(params)
        elif cmd == "get_profile":
            self.mobiapp.send_get_profile_request()
        elif cmd == "add_device":
            devsn = params[0]
            self.mobiapp.send_add_device_request(devsn)
        elif cmd == "del_device":
            devid = int(params[0])
            self.mobiapp.send_del_device_request(devid)
        elif cmd == "get_device_list":
            self.mobiapp.send_get_device_list_request()
        elif cmd == "modify_device_alias":
            devid = int(params[0])
            alias = params[1]
            self.mobiapp.send_modify_device_alias_request(devid, alias)
        elif cmd == "set_default_device":
            devid = int(params[0])
            self.mobiapp.send_change_default_device_request(devid)
        elif cmd == "get_device_info":
            uid = self.mobiapp.uid
            devid = int(params[0])
            self.mobiapp.send_common_message_request(uid, devid, DEVICE_INFO_GETTING_REQ, cmd)
        elif cmd == "get_device_status":
            uid = self.mobiapp.uid
            devid = int(params[0])
            self.mobiapp.send_common_message_request(uid, devid, DEVICE_STATUS_GETTING_REQ, cmd)
        elif cmd == "get_device_wlan_info":
            uid = self.mobiapp.uid
            devid = int(params[0])
            self.mobiapp.send_common_message_request(uid, devid, DEVICE_WLAN_INFO_GETTING_REQ, cmd)
        elif cmd == "get_device_sn":
            uid = self.mobiapp.uid
            devid = int(params[0])
            self.mobiapp.send_common_message_request(uid, devid, DEVICE_SN_GETTING_REQ, cmd)
        elif cmd == "device_charge":
            devid = int(params[0])
            self.mobiapp.send_device_charge_request(devid)
        elif cmd == "device_area_clean":
            devid = int(params[0])
            self.mobiapp.send_device_areaclean_request(devid)
        elif cmd == "device_auto_clean":
            devid = int(params[0])
            self.mobiapp.send_device_autoclean_request(devid)
        elif cmd == "device_manual_ctrl":
            devid = int(params[0])
            self.mobiapp.send_device_manual_ctrl_request(devid)
        elif cmd == "device_navigate_move":
            devid = int(params[0])
            self.mobiapp.send_device_navigate_move_request(devid)
        elif cmd == "device_point_clean":
            devid = int(params[0])
            self.mobiapp.send_device_point_clean_request(devid)
        elif cmd == "device_config_reset":
            devid = int(params[0])
            self.mobiapp.send_device_config_reset_request(devid)
        elif cmd == "device_wifi_ctrl":
            devid = int(params[0])
            self.mobiapp.send_device_wifi_ctrl_request(devid)
        elif cmd == "get_order_list":
            devid = int(params[0])
            self.mobiapp.send_get_order_list_request(devid)
        elif cmd == "set_order_list":
            devid = int(params[0])
            self.mobiapp.send_set_order_list_request(devid)
        elif cmd == "get_vwall_list":
            devid = int(params[0])
            self.mobiapp.send_get_vwall_list_request(devid)
        elif cmd == "set_vwall_list":
            devid = int(params[0])
            self.mobiapp.send_set_vwall_list_request(devid)
        elif cmd == "get_area_clean_info":
            devid = int(params[0])
            self.mobiapp.send_get_area_clean_request(devid)
        elif cmd == "map_ctrl":
            devid = int(params[0])
            map_type = int(params[1])
            self.mobiapp.send_map_ctrl_request(devid, map_type)
        elif cmd == "map_lidar_ctrl":
            devid = int(params[0])
            self.mobiapp.send_map_lidar_ctrl_request(devid)
        elif cmd == "device_upgrade_ctrl":
            devid = int(params[0])
            self.mobiapp.send_device_upgrade_ctrl_request(devid)
        elif cmd == "device_control_lock":
            devid = int(params[0])
            self.mobiapp.send_device_control_lock_request(devid)
        elif cmd == "query_clean_info":
            devid = int(params[0])
            start_time = int(params[1])
            end_time = int(params[2])
            self.mobiapp.send_query_device_data_request(devid, QUERY_DEVICE_CLEANINFO_REQ, start_time, end_time)
        elif cmd == "query_clean_map":
            devid = int(params[0])
            taskid = int(params[1])
            self.mobiapp.send_query_device_cleanmap_request(devid, taskid)
        elif cmd == "query_key_event":
            devid = int(params[0])
            start_time = int(params[1])
            end_time = int(params[2])
            self.mobiapp.send_query_device_data_request(devid, QUERY_DEVICE_KEY_EVENT_REQ, start_time, end_time)
        elif cmd == "query_fault_event":
            devid = int(params[0])
            start_time = int(params[1])
            end_time = int(params[2])
            self.mobiapp.send_query_device_data_request(devid, QUERY_DEVICE_FAULT_EVENT_REQ, start_time, end_time)
        else:
            print "Unknown command: ", cmd


    def validateCommand(self, cmd, params):
        if cmd not in commands_help.keys():
            print "Unknown command: ", cmd
            return False
        elif not self.validateParameters(cmd, params):
            self.showHelp([cmd])
            return False
        return True

    def para_j(self,para,num):     #params judge
        if (len(para) == num) and ('' not in para):
            return True
        else:
            return False

    def validateParameters(self, cmd, params):
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
            return False
        else:
            return True

    def showHelp(self, params):
        if len(params) == 0:
            #self.ui.Print(help)
            print help
        else:
            cmd = params[0]
            if cmd in commands_help.keys():
                #self.ui.Print("Usage: " + commands_help[cmd])
                print "Usage: ", commands_help[cmd]
            else:
                #self.ui.Print("Unknown command: " + cmd)
                print "Unknown command: ", cmd
