#!/usr/bin/python
#coding:utf-8
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import stdio
import time
import random
def shutdown():
    print "Terminating ...... "

mac = "%s:%s:%s:%s:%s:%s"
g_num = 123456789012351456
 
def gen_mac():
    global g_num
    g_num = g_num+1
    print g_num

    num = g_num
    lists = []

    for i in range(6):
	a=num%100
        lists.append(a)
	num=(num-a)/100
	
    mac_str = "%s:%s:%s:%s:%s:%s"%(lists[5],lists[4],lists[3],lists[2],lists[1],lists[0])    
    print mac_str


def showInfo():
    print random.randint(60,120)
def main():
    #print "running..."
    #myloop = task.LoopingCall(showInfo)
    myloop = task.LoopingCall(gen_mac)
    myloop.start(1)
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()
    #gen_mac()
if __name__ == "__main__":
    main()
