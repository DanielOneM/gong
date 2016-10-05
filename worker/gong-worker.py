# -*- coding:utf-8 -*-

import pika
from pika.adapters import twisted_connection
from twisted.internet import defer, reactor, protocol, task
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.portal import Portal
from smpp.twisted.config import SMPPServerConfig
from smpp.twisted.server import SMPPServerFactory


class GongWorker(object):

    def __init__(self, exchange=None,
                 topic=None,
                 incoming_q='send',
                 outgoing_q='received',
                 incoming_rk='send',
                 outgoing_rk='received',
                 rabbit_host=None,
                 rabbit_port=5672,
                 smpp_host='localhost',
                 smpp_port=2775,
                 smpp_user='default',
                 smpp_pass='default'):

        self.exchange = exchange
        self.topic = topic
        self.incoming_q = incoming_q
        self.incoming_rk = incoming_rk
        self.outgoing_q = outgoing_q
        self.outgoing_rk = outgoing_rk

        # start the components
        self.rabbit_server = self.start_rabbit(rabbit_host=rabbit_host,
                                               rabbit_port=rabbit_port)
        self.smpp_server = self.start_smpp(smpp_host, smpp_port,
                                           smpp_user=smpp_user,
                                           smpp_pass=smpp_pass)

    def start_rabbit(self, rabbit_host=None, rabbit_port=5672):

        parameters = pika.ConnectionParameters()
        cc = protocol.ClientCreator(reactor,
                                    twisted_connection.TwistedProtocolConnection,
                                    parameters)
        rabbit_server = cc.connectTCP(rabbit_host, rabbit_port)
        rabbit_server.addCallback(lambda protocol: protocol.ready)
        rabbit_server.addCallback(self.start_consuming)

        return rabbit_server

    def stop_rabbit(self):
        return self.rabbit_server.stopListening()

    def start_smpp(self, smpp_host, smpp_port, 
                   smpp_user='default', smpp_pass='default'):

        portal = Portal(self.SmppRealm())
        credential_checker = InMemoryUsernamePasswordDatabaseDontUse()
        credential_checker.addUser(smpp_user, smpp_pass)
        portal.registerChecker(credential_checker)
        cfg = SMPPServerConfig()

        self.factory = SMPPServerFactory(cfg, auth_portal=portal)
        self.proto = self.factory.buildProtocol((smpp_host, smpp_port))
        smpp_server = reactor.listenTCP(self.factory)

        return smpp_server

    def stop_smpp(self):
        return self.smpp_server.stopListening()

    @defer.inlineCallbacks
    def start_consuming(self, connection):
        channel = yield connection.channel()
        exchange = yield channel.exchange_declare(exchange=self.exchange,
                                                  type=self.topic,
                                                  durable=False)
        queue = yield channel.queue_declare(queue=self.incoming_q,
                                            auto_delete=False,
                                            exclusive=True)
        yield channel.queue_bind(exchange=self.exchange,
                                 queue=self.incoming_q,
                                 routing_key=self.incoming_rk)
        yield channel.basic_qos(prefetch_count=1)

        consume_tuple = yield channel.basic_consume(queue=self.incoming_q,
                                                    no_ack=False)
        self.queue_object, consumer_tag = consume_tuple

        work_task = task.LoopingCall(self.process_incoming, self.queue_object)
        work_task.start(0)

    @defer.inlineCallbacks
    def process_incoming(self, queue_object):
        ch, method, properties, body = yield queue_object.get()

        if body:
            print body

        yield ch.basic_ack(delivery_tag=method.delivery_tag)

    def stop_consuming(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def read_from_queue(self):
        pass

    def write_to_queue(self):
        pass

    def send_sms(self):
        pass

    def receive_sms(self):
        pass


@defer.inlineCallbacks
def read(self, queue_object):
    ch, method, properties, body = yield queue_object.get()

    if body:
        print body

    yield ch.basic_ack(delivery_tag=method.delivery_tag)



reactor.run()
