# -*- coding:utf-8 -*-
import pika
import signal
import sys
import os
import logging
import random
import string
#TODO: horrible hack used to solve import problems with vendor packages
sys.path.append(os.path.dirname(__file__))
sys.path.append("")

from pika.adapters import twisted_connection
from twisted.python import usage
from twisted.internet import defer, reactor, protocol, task
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.portal import Portal
from twisted.cred.portal import IRealm
from zope.interface import implements

from gong.vendor.twisted.server import SMPPServerFactory
from gong.vendor.twisted.config import SMPPServerConfig
from gong.vendor.pdu.operations import DeliverSM


class SmppRealm(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        return ('SMPP', avatarId, lambda: None)


class GongWorker(object):
    """SMSC simulator server."""

    def __init__(self, name=None,
                 exchange='gong',
                 recv_rk='received',
                 send_rk='send',
                 rabbit_host='localhost',
                 rabbit_port=5672,
                 smpp_port=None,
                 smpp_pass='default',
                 log=None):
        """Initialize the worker."""
        if name is None:
            raise ValueError('GongWorker node needs a name.')
        if smpp_port is None:
            raise ValueError('GongWorker needs a port number for \
                the local port to listen to')

        try:
            self.smpp_port = int(smpp_port)
        except Exception:
            raise ValueError('GongWorker SMPP port number needs \
                to be an integer')

        if name is not None:
            self.name = name
        else:
            self.name = ''.join(
                random.choice(string.ascii_letters + string.digits)
                for _ in range(8))

        self.exchange = exchange
        self.recv_rk = recv_rk
        self.send_q = '{}.{}'.format(send_rk, name)
        self.send_rk = name
        self.rabbit_host = rabbit_host
        self.rabbit_port = int(rabbit_port)
        self.smpp_pass = smpp_pass
        self.components = {}

        if log is None:
            self.log = logging.getLogger('<gongwrk-{}>'.format(self.name))
        else:
            self.log = log

        self.log.debug(self.__dict__)

    def start_rabbit(self, rabbit_host, rabbit_port):
        """Start the rabbit server connection."""
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(host=rabbit_host,
                                               port=rabbit_port,
                                               credentials=credentials)
        cc = protocol.ClientCreator(reactor,
                                    twisted_connection.TwistedProtocolConnection,
                                    parameters)
        rabbit_server = cc.connectTCP(rabbit_host, rabbit_port)
        rabbit_server.addCallback(lambda protocol: protocol.ready)
        rabbit_server.addCallback(self.start_channel)

        return rabbit_server

    def stop_rabbit(self):
        """Stop the rabbit server connection."""
        return self.components['rabbit_server'].stopListening()

    def start_smpp(self, smpp_port, smpp_pass):
        """Start the smpp server."""
        portal = Portal(SmppRealm())
        credential_checker = InMemoryUsernamePasswordDatabaseDontUse()
        credential_checker.addUser(self.name, smpp_pass)
        portal.registerChecker(credential_checker)
        cfg = SMPPServerConfig(msgHandler=self.process_incoming,
                               systems={self.name: {"max_bindings": 1}})

        self.smpp_factory = SMPPServerFactory(cfg, auth_portal=portal)
        smpp_server = reactor.listenTCP(smpp_port, self.smpp_factory)

        return smpp_server

    def stop_smpp(self):
        """Stop the smpp server."""
        return self.components['smpp_server'].stopListening()

    @defer.inlineCallbacks
    def start_channel(self, connection):
        """Start a channel for the RabbitMQ connection."""
        self.log.debug('starting rmq channel')
        self.channel = yield connection.channel()
        if not self.channel:
            self.log.critical('No connection to RabbitMQ. Exiting.')
            self.stop()
        exchange = yield self.channel.exchange_declare(exchange=self.exchange,
                                                       type='topic',
                                                       durable=True)
        yield self.start_consuming()

    @defer.inlineCallbacks
    def start_consuming(self):
        """Start consuming from the outgoing queue."""
        queue = yield self.channel.queue_declare(queue=self.send_q,
                                                 auto_delete=False,
                                                 exclusive=True)
        yield self.channel.queue_bind(exchange=self.exchange,
                                      queue=self.send_q,
                                      routing_key=self.send_rk)
        yield self.channel.basic_qos(prefetch_count=1)

        consume_tuple = yield self.channel.basic_consume(queue=self.send_q,
                                                         no_ack=True)
        queue_object, consumer_tag = consume_tuple

        self.log.debug('starting consumer')
        work_task = task.LoopingCall(self.process_outgoing, queue_object)
        work_task.start(0.01)

    @defer.inlineCallbacks
    def process_outgoing(self, queue_object):
        """Send messages from the outgoing queue through the smpp server."""
        ch, method, properties, body = yield queue_object.get()
        self.log.debug('Received outgoing msg: %s', body)

        body = eval(body)
        # TODO: create a correct PDU with all the necessary info
        pdu = DeliverSM(
            source_addr=body['src'],
            destination_addr=body['dst'],
            short_message=body['sms'].encode('utf8'),
        )

        binding = self.smpp_factory.getBoundConnections(self.name).getNextBindingForDelivery()
        if binding is not None:
            yield binding.sendPDU(pdu)

        # yield ch.basic_ack(delivery_tag=method.delivery_tag)

    @defer.inlineCallbacks
    def process_incoming(self, smpp, pdu):
        """Send messages received by the smpp server to the incoming queue."""
        yield self.channel.basic_publish(exchange=self.exchange,
                                         routing_key=self.recv_rk,
                                         body=pdu)

    def start(self):
        """Start the worker."""
        # start the components
        self.log.debug('starting rmq')
        self.components['rabbit_server'] = self.start_rabbit(self.rabbit_host,
                                                             self.rabbit_port)
        self.log.debug('starting smpp')
        self.components['smpp_server'] = self.start_smpp(self.smpp_port,
                                                         self.smpp_pass)
        self.log.debug('setup completed')

    def stop(self):
        """Stop the worker."""
        if reactor.running:
            reactor.stop()

    def gentle_stop(self, a, b):
        """Handle an external stop signal."""
        return self.stop()


class Options(usage.Options):
    """Command-line options for GongWorker."""

    optParameters = [
        ['name', 'n', None, 'Name for the GongWorker node'],
        ['exchange', 'e', 'gong', 'RabbitMQ exchange name'],
        ['recv_rk', 'i', 'received', 'Queue to store received messages'],
        ['send_rk', 'o', 'send', 'Queue used to submit messages to be sent'],
        ['rabbit_host', '', 'localhost', 'RabbitMQ hostname'],
        ['rabbit_port', '', 5672, 'RabbitMQ port'],
        ['smpp_port', 'p', None, 'Port to use for the SMPP server'],
        ['smpp_pass', '', 'default', 'Password for the SMPP server user']
    ]


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    try:
        options = Options()
        options.parseOptions()

        gongd = GongWorker(**options)
        # Setup signal handlers
        signal.signal(signal.SIGINT, gongd.gentle_stop)
        # Start Gong Worker daemon
        gongd.start()

        reactor.run()
    except usage.UsageError, errortext:
        print '%s: %s' % (sys.argv[0], errortext)
        print '%s: Try --help for usage details.' % (sys.argv[0])

    except Exception as e:
        print e
