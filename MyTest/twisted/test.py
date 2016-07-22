#!/usr/bin/python
#coding:utf-8
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import stdio
import time
import random
def shutdown():
    print "Terminating ...... "

def showInfo():
    print random.randint(60,120)
def main():
    #print "running..."
    num = 1
    myloop = task.LoopingCall(showInfo)
    myloop.start(1)
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()
if __name__ == "__main__":
    main()
