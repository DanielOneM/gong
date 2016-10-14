import pika
from pika import exceptions
import logging
from pika.adapters import twisted_connection
from twisted.internet import defer, reactor, protocol,task

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('gongworker')


@defer.inlineCallbacks
def run(connection):

    channel = yield connection.channel()
    log.debug('channel ready')

    exchange = yield channel.exchange_declare(exchange='topic_link',type='topic')
    log.debug('exchange declared')

    queue = yield channel.queue_declare(queue='hello', auto_delete=False, exclusive=False)
    log.debug('queue declare')

    yield channel.queue_bind(exchange='topic_link',queue='hello',routing_key='hello.world')
    log.debug('queue bind declare')

    yield channel.basic_qos(prefetch_count=1)

    channel.basic_publish(exchange='topic_link', routing_key='hello.world', body='something')
    log.debug('basic publish')

    queue_object, consumer_tag = yield channel.basic_consume(queue='hello',no_ack=False)
    log.debug('queue object started')

    l = task.LoopingCall(read, queue_object)

    l.start(0.01)


@defer.inlineCallbacks
def read(queue_object):

    log.debug('reading queue object')
    ch,method,properties,body = yield queue_object.get()

    if body:
        log.debug('msg body: %s', body)

    yield ch.basic_ack(delivery_tag=method.delivery_tag)

    reactor.stop()


def fail(failure):
    log.debug(failure)
    reactor.stop()


credentials = pika.PlainCredentials('test','test')
parameters = pika.ConnectionParameters(host='172.25.0.2', port=5672, credentials=credentials)
cc = protocol.ClientCreator(reactor, twisted_connection.TwistedProtocolConnection, parameters)
d = cc.connectTCP('172.25.0.2', 5672)
d.addCallback(lambda protocol: protocol.ready)
d.addErrback(fail)
d.addCallback(run)
log.debug('starting reactor')
reactor.run()
