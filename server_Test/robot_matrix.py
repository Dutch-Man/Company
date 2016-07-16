#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#

import optparse

from twisted.internet import stdio

from robot_factory import *
from robot_controller import *

g_options = None

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
    log_filename = "robot_test_%s_%d.log" % (host, port)

    RobotMatrix.robot_factory = RobotFactory(host, port, log_filename)
    controller = Controller(RobotMatrix.robot_factory)
    cui = CUI(controller)
    stdio.StandardIO(cui)

    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()


if __name__ == '__main__':
    main()
