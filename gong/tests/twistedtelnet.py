"""A module with helpers needed to manage Jasmin."""

import logging
from functools import partial

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.conch.telnet import TelnetTransport, TelnetProtocol


class TelnetChecker(TelnetProtocol):
    """Implementation of a check-if-alive monitor over telnet."""

    delimiter = '\n'
    logged_in = False
    prompt = 'jcli : '
    active_callback = None

    def write_command(self, command):
        """Send a telnet command."""
        self.transport.write(command + self.delimiter)

    def dataReceived(self, bytes):
        """
        Process received telnet data.

        The method automatically closes the connection if there are
        no more commands to be transmitted.
        """
        self.factory.log.debug('received:' + repr(bytes))
        if len(bytes) == 0:
            self.factory.log.debug('no msg contents')
            return

        if not self.logged_in:
            self.telnet_login(bytes,
                              self.factory.configs['user'],
                              self.factory.configs['pwd'])
            return

        if self.active_callback is not None:
            self.process_callback(bytes)

        self.factory.log.debug('processing %s left commands',
                               len(self.factory.commands))
        if len(self.factory.commands) == 0:
            self.telnet_quit()
        else:
            self.telnet_commands(bytes)

    def process_callback(self, bytes):
        """Process the callbacks registered to each command."""
        if isinstance(self.active_callback, str):
            method = getattr(self, self.active_callback)
        else:
            method = self.active_callback

        res = method(bytes)

        if isinstance(res, tuple):
            if all(res):
                self.telnet_quit()

        self.active_callback = None
        self.factory.log.debug('finished callback')

    def telnet_login(self, bytes, user, password):
        """Login the user."""
        login_commands = [
            ('auth', ''),
            ('username', user),
            ('password', password)
        ]

        for key in login_commands:
            if key[0] in repr(bytes).lower():
                self.write_command(key[1])
                if key == login_commands[-1]:
                    self.logged_in = True
                return

    def telnet_commands(self, bytes):
        """Transmit one command from a sequence."""
        if self.prompt in repr(bytes).lower():
            key = self.factory.commands.pop(0)
            self.factory.log.debug('processing command: %s', key[0])

            self.write_command(key[0])
            if len(key) > 1:
                self.active_callback = key[1]
            self.factory.log.debug('sent:' + repr(key[0]))

    def telnet_enter_submenu(self, bytes):
        """Change prompt reference."""
        new_prompt = '> '
        if new_prompt in bytes:
            self.prev_prompt = self.prompt
            self.prompt = new_prompt

    def telnet_exit_submenu(self, bytes):
        """Change prompt reference to normal state."""
        if self.prev_prompt not in bytes:
            self.prompt = self.prev_prompt

    def telnet_quit(self):
        """Close the connection and stop the reactor."""
        self.factory.log.debug('closing connection.')
        self.write_command('quit')
        reactor.stop()


class TelnetFactory(ClientFactory):
    """Implementation of a telnet factory checker."""

    def __init__(self, commandlist, logger, configs):
        """Override init method to include needed attributes."""
        self.commands = commandlist
        self.log = logger

        self.configs = configs

    def buildProtocol(self, addr):
        """Override method to add factory as attribute."""
        protocol = TelnetTransport(TelnetChecker)
        protocol.factory = self
        return protocol


def is_alive(target, bytes):
    """Used to extract the connector info from a listing."""
    logger.debug('checking:' + repr(bytes))
    out = str(bytes)
    data = [item for item in out.split('\r\r\n')
            if item.startswith('#')]

    results = {}
    for item in data[1:]:
        item = item.split()
        if item[0].replace('#', '') == target:
            results = {
                'connector_id': item[0].replace('#', ''),
                'service_status': item[1],
                'session_status': item[2],
                'starts': item[3],
                'stops': item[4]
            }

    if results == {}:
        return False, False

    service_ok = results['service_status'] == 'started'
    session_ok = results['session_status'] != 'None'
    status = True if service_ok and session_ok else False

    logger.info('Connection to %s is alive: %s', target, status)

    registered = True if results != {} else False

    return status, registered


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('TelnetChecker')

    target = 'gong'
    gong_user = 'test'
    gong_pass = 'default'
    gong_host = '172.25.0.4'
    gong_port = '2775'

    commands = [
        ('smppccm -l', partial(is_alive, target)),
        ('smppccm -r {}'.format(target),),
        ('smppccm -a', 'telnet_enter_submenu'),
        ('cid {}'.format(target),),
        ('username {}'.format(gong_user),),
        ('password {}'.format(gong_pass),),
        ('host {}'.format(gong_host),),
        ('port {}'.format(gong_port),),
        ('ok', 'telnet_exit_submenu'),
        ('smppccm -1 {}'.format(target),)
    ]

    configs = {
        'user': 'jcliadmin',
        'pwd': 'jclipwd',
    }

    factory = TelnetFactory(commands, logger, configs)
    reactor.connectTCP('localhost', 8990, factory)
    reactor.run()
