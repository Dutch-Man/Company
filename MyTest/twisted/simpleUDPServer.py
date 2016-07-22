#!/usr/bin/python
'''
import sys
from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import Protocol 
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor

from twisted.internet.protocol import tagramProtocol
#class CmdProtocol(LineReceiver):
class CmdProtocol(DatagramProtocol):
    num_clients = 0
    def connectionMade(self):
        self.transport.write("Hello client, I am the server!\n")
	CmdProtocol.num_clients += 1
        CmdProtocol.num_clients 
	print "Client%d:"%CmdProtocol.num_clients, self.transport.getPeer()
	
    def datagramReceived(self, datagram, addr):
	print "Client :",addr
class MyFactory(ServerFactory):

    protocol = CmdProtocol

def main():
    reactor.listenUDP(9999, MyFactory())
    reactor.run()
if __name__ == "__main__":
    main()
'''


from twisted.internet.protocol import DatagramProtocol

from twisted.internet import reactor

 

class Echo(DatagramProtocol):

   

    def datagramReceived(self, data, (host, port)):

        print "received %s from %s:%d" % (data, host, port)

        self.transport.write(data, (host, port))

 

reactor.listenUDP(9999, Echo())

reactor.run()

