#!/usr/bin/python
#coding:utf-8
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import stdio
import time

def shutdown():
    print "Terminating ...... "

def showTime(num1,num2,num3):
#    print time.strptime(a, "%Y-%m-%d %H:%M:%S") 
    print num1,num2,num3
    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
def main():
    #print "running..."
    num = 1
    myloop = task.LoopingCall(showTime,num,num+1,num+2)
    myloop.start(1)
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()
if __name__ == "__main__":
    main()
