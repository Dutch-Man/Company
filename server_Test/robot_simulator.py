#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#

import optparse
from robot_factory import *

g_options = None


def parse_args():
    usage = """usage: %prog [options] [hostname]:port"""

    parser = optparse.OptionParser(usage)

    help = "The device serial number of Robot"
    parser.add_option('--sn', help=help, default="")

    help = "Register device, true or false"
    parser.add_option('--reg', help=help, default="true")

    global g_options
    g_options, args = parser.parse_args()
    print "options: ", g_options

    if len(args) != 1:
        parser.error('Provide exactly one server address.')
    if not g_options.sn:
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

    return parse_address(args[0])

def startup():
    registered = (True if g_options.reg == 'true' else False)
    RobotMatrix.robot_factory.build_robot(g_options.sn, registered)
    RobotMatrix.robot_factory.run_robot(g_options.sn)

def shutdown():
    print 'Terminating...'

def main():
    host, port = parse_args()
    RobotMatrix.robot_factory = RobotFactory(host, port)

    reactor.addSystemEventTrigger('after', 'startup', startup)
    reactor.addSystemEventTrigger('after', 'shutdown', shutdown)
    reactor.run()


if __name__ == '__main__':
    main()
