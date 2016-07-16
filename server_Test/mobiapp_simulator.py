#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#

import optparse
from mobiapp_factory import *

g_options = None


def parse_args():
    usage = """usage: %prog [options] [hostname]:port"""

    parser = optparse.OptionParser(usage)

    help = "The useranme of MobiApp"
    parser.add_option('--username', help=help, default="")

    help = "The password of MobiApp"
    parser.add_option('--password', help=help, default="")

    global g_options
    g_options, args = parser.parse_args()
    print "options: ", g_options

    if len(args) != 1:
        parser.error('Provide exactly one server address.')
    if not g_options.username:
        parser.error('Please provide username with --username.')
    if not g_options.password:
        parser.error('Please provide password with --password.')

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
    MobiAppMatrix.mobiapp_factory.build_mobiapp(g_options.username, g_options.password)
    MobiAppMatrix.mobiapp_factory.run_mobiapp(g_options.username, True)

def shutdown():
    print 'Terminating...'

def main():
    host, port = parse_args()
    MobiAppMatrix.mobiapp_factory = MobiAppFactory(host, port)

    reactor.addSystemEventTrigger('after', 'startup', startup)
    reactor.addSystemEventTrigger('after', 'shutdown', shutdown)
    reactor.run()


if __name__ == '__main__':
    main()
