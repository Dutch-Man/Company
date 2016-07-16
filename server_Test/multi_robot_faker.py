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

import robot_faker

connector_list = []

def close_all_connection():
   for connector in connector_list:
       connector.disconnect()

def shutdown():
    print 'Terminating...'
    close_all_connection()
    #reactor.removeAll()
    #reactor.stop()

def main():
    server_addr, num = robot_faker.parse_args()
    local_host, local_port = server_addr
    factory = robot_faker.RobotProtocolFactory()
    global connector_list

    for i in range(1,int(num)+1):
        connector = reactor.connectTCP(local_host, local_port, factory,100)
        #time.sleep(0.1)
        connector_list.append(connector)
        if i % 100 == 0:
            print "create client: %d" % i

    print 'Robot started, connect to %s:%d.' % server_addr
    
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()
    

if __name__ == '__main__':
    main()
