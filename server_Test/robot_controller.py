# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#
from twisted.internet import reactor
from twisted.protocols import basic

class Controller:
    def __init__(self, robot_factory):
        self.ui = None
        self.robot_factory = robot_factory

    def set_ui(self, ui):
        self.ui = ui

    def handleCommand(self, cmd, params):
        if cmd in ["exit", "quit"]:
            reactor.stop()
        elif cmd in ["help", "?"]:
            self.ui.showHelp(params)
        elif cmd == "create_robot":
            devsn = params[0]
            registered = params[1] if len(params) == 2 else False
            self.robot_factory.build_robot(devsn, registered)
        elif cmd == "create_robot_batch":
            devsn_prefix = params[0]
            begin_idx = int(params[1])
            end_idx = int(params[2])
            self.robot_factory.build_robot_batch(devsn_prefix, begin_idx, end_idx)
        elif cmd == "set_default_robot":
            devsn = params[0]
            self.robot_factory.set_default_robot(devsn)
        elif cmd == "run_robot":
            devsn = params[0] if len(params) == 1 else self.robot_factory.get_default_robot()
            self.robot_factory.run_robot(devsn)
        elif cmd == "stop_robot":
            devsn = params[0] if len(params) == 1 else self.robot_factory.get_default_robot()
            self.robot_factory.stop_robot(devsn)
        elif cmd == "show_robot_info":
            devsn = params[0] if len(params) == 1 else self.robot_factory.get_default_robot()
            self.robot_factory.show_robot_info(devsn)
        elif cmd == "run_all_robots":
            self.robot_factory.run_all_robots()
        elif cmd == "stop_all_robots":
            self.robot_factory.stop_all_robots()
        elif cmd == "list_robots":
            which = params[0] if len(params) == 1 else "all"
            self.robot_factory.list_robots(which)
        elif cmd == "flush_log":
            self.robot_factory.flush_log()
        elif cmd == "change_logfile":
            filename = params[0]
            self.robot_factory.change_logfile(filename)
        elif cmd == "info":
            self.robot_factory.show_info()
        else:
            print "Unknown command: ", cmd

class CUI(basic.LineReceiver):
    from os import linesep as delimiter

    commands_help = \
            { \
            '?'                     : '? [COMMAND]', \
            'help'                  : 'help [COMMAND]', \
            'exit'                  : 'exit', \
            'quit'                  : 'quit', \
            'create_robot'          : 'create_robot <DEVICE SN> [0|1], the second parameter point out REGISTERED', \
            'create_robot_batch'    : 'create_robot_batch <DEVICE SN PREFIX> <BEGIN INDEX> <END INDEX>', \
            'set_default_robot'     : 'set_default_robot <DEVICE SN>', \
            'run_robot'             : 'run_robot [DEVICE SN], Must setting default device before if not provide DEVICE SN', \
            'stop_robot'            : 'stop_robot [DEVICE SN], Must setting default device before if not provide DEVICE SN', \
            'show_robot_info'       : 'show_robot_info [DEVICE SN], Must setting default device before if not provides DEVICE SN', \
            'run_all_robots'        : 'run_all_robots', \
            'stop_all_robots'       : 'stop_all_robots', \
            'list_robots'           : 'list_robots [\'all\'|\'stopped\'|\'running\'|\'scheduling\']', \
            'flush_log'             : 'flush_log', \
            'change_logfile'        : 'change_logfile <FILE NAME>', \
            'info'                  : 'info', \
            }
    help = \
"Commands: \n\
  ?                      : %s\n\
  help                   : %s\n\
  exit                   : %s\n\
  quit                   : %s\n\
  create_robot           : %s\n\
  create_robot_batch     : %s\n\
  set_default_robot      : %s\n\
  run_robot              : %s\n\
  stop_robot             : %s\n\
  show_robot_info        : %s\n\
  run_all_robots         : %s\n\
  stop_all_robots        : %s\n\
  list_robots            : %s\n\
  flush_log              : %s\n\
  change_logfile         : %s\n\
  info                   : %s\n\
  " % (\
  commands_help['?'],\
  commands_help['help'],\
  commands_help['exit'],\
  commands_help['quit'],\
  commands_help['create_robot'],\
  commands_help['create_robot_batch'],\
  commands_help['set_default_robot'],\
  commands_help['run_robot'],\
  commands_help['stop_robot'],\
  commands_help['show_robot_info'],\
  commands_help['run_all_robots'],\
  commands_help['stop_all_robots'],\
  commands_help['list_robots'],\
  commands_help['flush_log'],\
  commands_help['change_logfile'],\
  commands_help['info'],\
  )

    def __init__(self, controller):
        self.controller = controller
        self.controller.set_ui(self)

    def connectionMade(self):
        self.transport.write('>>> ')

    def lineReceived(self, line):
        if len(line) > 0:
            cmd, params = self.parseInput(line)
            #print "( cmd: %s, params: %s )" % (cmd, params)
            success = self.validateCommand(cmd, params)
            if success:
                self.controller.handleCommand(cmd, params)
        self.transport.write(">>> ")

    def parseInput(self, line):
        list = line.strip().split(' ')
        cmd = list[0]
        params = list[1:]
        return cmd, params

    def validateCommand(self, cmd, params):
        if cmd not in self.commands_help.keys():
            self.sendLine("Unknown command: " + cmd)
            return False
        elif not self.validateParameters(cmd, params):
            self.showHelp([cmd])
            return False
        return True

    def validateParameters(self, cmd, params):
        if cmd == "create_robot":
            return len(params) == 1 or len(params) == 2
        elif cmd == "create_robot_batch":
            return len(params) == 3
        elif cmd == "set_default_robot":
            return len(params) == 1
        elif cmd == "run_robot" or \
            cmd == "stop_robot" or \
            cmd == "show_robot_info" :
            return (len(params) == 0 and self.controller.robot_factory.has_default_robot()) or len(params) == 1
        elif cmd == "list_robots":
            return params[0] in ['all', 'stopped', 'running', 'scheduling'] if len(params) == 1 else True
        elif cmd == "change_logfile":
            return len(params) == 1
        else:
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
