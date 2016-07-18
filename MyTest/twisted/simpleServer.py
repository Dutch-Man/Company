#!/usr/bin/python

import sys
from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import Protocol 
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor

#class CmdProtocol(LineReceiver):
class CmdProtocol(Protocol):
    num_clients = 0
    def connectionMade(self):
        self.transport.write("Hello client, I am the server!\n")
	CmdProtocol.num_clients += 1
        CmdProtocol.num_clients 
	print "Client%d:"%CmdProtocol.num_clients, self.transport.getPeer()
	
    def dataReceived(self,data):
	print "Client :",data
class MyFactory(ServerFactory):

    protocol = CmdProtocol

def main():
    reactor.listenTCP(9999, MyFactory())
    reactor.run()
if __name__ == "__main__":
    main()
