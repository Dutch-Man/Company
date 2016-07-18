#!/usr/bin/python

from twisted.internet.protocol import Protocol, ClientFactory
from sys import stdout

class Echo(Protocol):
    def dataReceived(self, data):
        #stdout.write(data)
	print "Server :",data
    def connectionMade(self):
	Peer = self.transport.getPeer()
	print "Server :",Peer
	self.transport.write("Hello server, I am a client!\r\n")
	
	#print dir(self.transport)
class EchoClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)

from twisted.internet import reactor
from twisted.internet import task 

def makeTCP():
    global num
    num += 1
    host = "0.0.0.0"
    port = 9999
    reactor.connectTCP(host, port, EchoClientFactory())
    if num == 10000:

    # We looped enough times.
	global loop
	loop.stop() 
num = 0
 
def main():
    global num
    host = "0.0.0.0"
    port = 9999
    global loop
    loop = task.LoopingCall(makeTCP)
    loopDeferred = loop.start(0.01)
    #reactor.connectTCP(host, port, EchoClientFactory())
    reactor.run()

if __name__ == "__main__":
    main()
