import logging
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.conch.telnet import TelnetTransport, TelnetProtocol

logging.basicConfig(level=logging.DEBUG)


class TelnetPrinter(StatefulTelnetProtocol):
    def dataReceived(self, bytes):
        print 'received:' + repr(bytes)
        if 'username' in repr(bytes).lower():
            self.transport.write('jcliadmin\n')
        if 'password' in repr(bytes).lower():
            self.transport.write('jclipwd\n')
        if 'jcli :' in repr(bytes).lower():
            self.transport.write('smppccm -l\n')
        else:
            self.transport.write('\n')

class TelnetFactory(ClientFactory):
    def buildProtocol(self, addr):
        return TelnetTransport(TelnetPrinter)

reactor.connectTCP('localhost', 8990, TelnetFactory())
reactor.run()