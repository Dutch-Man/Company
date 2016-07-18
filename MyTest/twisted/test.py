#!/usr/bin/python
#coding:utf-8
from twisted.internet import task
from twisted.internet import reactor
from twisted.internet import stdio


def shutdown():
    print "Terminating ...... "
def main():
    #print "running..."
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
    reactor.run()
if __name__ == "__main__":
    main()
