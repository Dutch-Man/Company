#!/usr/bin/python

import sys
from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol 
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor

p_file = open("connection_failed.txt","w+")
#class CmdProtocol(LineReceiver):
class CmdProtocol(Protocol):
    num = 0
    def connectionMade(self):
        #self.transport.write("bbbbb")
        CmdProtocol.num += 1
        print CmdProtocol.num
        #reactor.iterate()

        #p_file.write("%d\n"%CmdProtocol.num)
    def dataReceived(self,data):
        print data 
class MyFactory(ClientFactory):

    protocol = CmdProtocol
    def clientConnectionFailed(self,connector, reason):
        global p_file
        p_file.write("[Factory] Make connection failed (%s): %s" % \
        (connector.getDestination(), reason))
#   def clientConnectionLost(self, connector, reason):
#       my_print("[RobotProtocolFactory] Connection lost (%s): %s" % \
#       (connector.getDestination(), reason), "./connection_lost.txt")
def main():
    for i in range(10000):
#        reactor.connectTCP("127.0.0.1",9999, MyFactory())
        reactor.connectTCP("120.76.189.9",9999, MyFactory(),100)
    reactor.run()
if __name__ == "__main__":
    main()
