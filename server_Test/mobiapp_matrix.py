#!/usr/bin/python
#coding:utf-8
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#

import optparse
from twisted.internet import reactor
from twisted.internet import stdio
from twisted.protocols import basic

from mobiapp_factory import *
from mobiapp_controller import commands_help as mobiapp_commands_help


g_options = None

class Controller:
    def __init__(self, mobiapp_factory):
        self.ui = None
        self.mobiapp_factory = mobiapp_factory
        self.select_mobiapp = False

    def set_ui(self, ui):
        self.ui = ui

    def handleCommand(self, cmd, params):
        if self.select_mobiapp:
            if cmd[0] == ".":
                self.handle_matrix_command(cmd[1:], params)
            else:
                self.handle_mobiapp_command(cmd, params)
        else:
            self.handle_matrix_command(cmd, params)

    def handle_matrix_command(self, cmd, params):
        if cmd in ["exit", "quit"]:
            reactor.stop()
        elif cmd in ["help", "?"]:
            self.ui.showHelp(params)
        elif cmd == "create":
            username = params[0]
            password = params[1]
            self.mobiapp_factory.build_mobiapp(username, password)
        elif cmd == "batch_create":
            username_prefix = params[0]
            begin_idx = int(params[1])
            end_idx = int(params[2])
            self.mobiapp_factory.build_mobiapp_batch(username_prefix, begin_idx, end_idx)
        elif cmd == "select":
            username = params[0]
            success = self.mobiapp_factory.set_default_mobiapp(username)
            if success:
                self.ui.set_prompt("%s >>> " % username)
                self.select_mobiapp = True
        elif cmd == "run":
            username = params[0] if len(params) == 1 else self.mobiapp_factory.get_default_devsn()
            self.mobiapp_factory.run_mobiapp(username)
        elif cmd == "stop":
            username = params[0] if len(params) == 1 else self.mobiapp_factory.get_default_devsn()
            self.mobiapp_factory.stop_mobiapp(username)
        elif cmd == "show_info":
            username = params[0] if len(params) == 1 else self.mobiapp_factory.get_default_devsn()
            self.mobiapp_factory.show_mobiapp_info(username)
        elif cmd == "run_all":
            self.mobiapp_factory.run_all_mobiapps()
        elif cmd == "stop_all":
            self.mobiapp_factory.stop_all_mobiapps()
        elif cmd == "list":
            which = (params[0] if len(params) == 1 else "all")
            self.mobiapp_factory.list_mobiapps(which)
        elif cmd == "info":
            self.mobiapp_factory.show_info()
        elif cmd == "flushlog":
            self.mobiapp_factory.flush_log()
        elif cmd == "change_logfile":
            filename = params[0]
            self.mobiapp_factory.change_logfile(filename)
        elif cmd == "info":
            self.mobiapp_factory.show_info()
        else:
            print "Unknown command: ", cmd

    def handle_mobiapp_command(self, cmd, params):
        if cmd == "unselect":
            self.select_mobiapp = False
            self.mobiapp_factory.clear_default_mobiapp()
            self.ui.set_prompt(">>> ")
        else:
            mobiapp = self.mobiapp_factory.get_default_mobiapp()
            if mobiapp:
                mobiapp.get_controller().handleCommand(cmd, params)
            else:
                print "Have no default MobiApp"

class CUI(basic.LineReceiver):
    from os import linesep as delimiter

    commands_help = \
            { \
            '?'             : '? [COMMAND]', \
            'help'          : 'help [COMMAND]', \
            'exit'          : 'exit', \
            'quit'          : 'quit', \
            'create'        : 'create <USERNAME> <PASSWORD>', \
            'batch_create'  : 'batch_create <USERNAME PREFIX> <BEGIN INDEX> <END INDEX>', \
            'select'        : 'select <USERNAME>', \
            'unselect'      : 'unselect', \
            'run'           : 'run [USERNAME], Must setting default MobiApp before if not provides USERNAME', \
            'stop'          : 'stop [USERNAME], Must setting default MobiApp before if not provides USERNAME', \
            'show_info'     : 'show_info [USERNAME], Must setting default MobiApp before if not provides USERNAME', \
            'run_all'       : 'run_all', \
            'stop_all'      : 'stop_all', \
            'list'          : 'list [\'all\'|\'stopped\'|\'running\'|\'scheduling\']', \
            'flushlog'      : 'flushlog', \
            'change_logfile': 'change_logfile <FILE NAME>', \
            'info'          : 'info', \
            }
    help = \
"Commands: \n\
  ?                 : %s\n\
  help              : %s\n\
  exit              : %s\n\
  quit              : %s\n\
  create            : %s\n\
  batch_create      : %s\n\
  select            : %s\n\
  unselect          : %s\n\
  run               : %s\n\
  stop              : %s\n\
  show_info         : %s\n\
  run_all           : %s\n\
  stop_all          : %s\n\
  list              : %s\n\
  flushlog          : %s\n\
  change_logfile    : %s\n\
  info              : %s\n\
  " % (\
  commands_help['?'],\
  commands_help['help'],\
  commands_help['exit'],\
  commands_help['quit'],\
  commands_help['create'],\
  commands_help['batch_create'],\
  commands_help['select'],\
  commands_help['unselect'],\
  commands_help['run'],\
  commands_help['stop'],\
  commands_help['show_info'],\
  commands_help['run_all'],\
  commands_help['stop_all'],\
  commands_help['list'],\
  commands_help['flushlog'],\
  commands_help['change_logfile'],\
  commands_help['info'],\
  )


    def __init__(self, controller):
        self.controller = controller
        self.controller.set_ui(self)
        self.prompt = ">>> "

    def set_prompt(self, prompt):
        self.prompt = prompt

    def connectionMade(self):
        self.transport.write(self.prompt)

    def lineReceived(self, line):
        if len(line) > 0:
            cmd, params = self.parseInput(line)
            #print "( cmd: %s, params: %s )" % (cmd, params)
            success = self.validateCommand(cmd, params)
            if success:
                self.controller.handleCommand(cmd, params)
        self.transport.write(self.prompt)

    def parseInput(self, line):
        list = line.strip().split(' ')
        cmd = list[0]
        params = list[1:]
        return cmd, params

    def validateCommand(self, cmd, params):
        if cmd[0] == ".":
            cmd = cmd[1:]
        if cmd not in self.commands_help.keys() and cmd not in mobiapp_commands_help.keys():
            self.sendLine("Unknown command: " + cmd)
            return False
        elif not self.validateParameters(cmd, params):
            self.showHelp([cmd])
            return False
        return True

    def validateParameters(self, cmd, params):
        if cmd == "create":
            return len(params) == 2
        elif cmd == "batch_create":
            return len(params) == 3
        elif cmd == "select":
            return len(params) == 1
        elif cmd == "run" or \
            cmd == "stop" or \
            cmd == "show_info" :
            return (len(params) == 0 and self.controller.mobiapp_factory.has_default_mobiapp()) or len(params) == 1
        elif cmd == "list":
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

def parse_args():
    usage = """usage: %prog [options] [hostname]:port"""

    parser = optparse.OptionParser(usage)

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


def shutdown():
    print 'Terminating...'

def main():
    host, port = parse_args()
    log_filename = "mobiapp_test_%s_%d.log" % (host, port)

    MobiAppMatrix.mobiapp_factory = MobiAppFactory(host, port, log_filename)
    controller = Controller(MobiAppMatrix.mobiapp_factory)
    cui = CUI(controller)
    stdio.StandardIO(cui)

    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()


if __name__ == '__main__':
    main()
