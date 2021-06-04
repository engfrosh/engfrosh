import pika
import logging
import json


logger = logging.getLogger("RabbitSender")


class RabbitMQSender():
    def __init__(self, queue, host: str = "localhost", exchange=''):
        self.exchange = exchange
        self.queue = queue
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        logger.info(f"Connection started on {host} with queue: {queue} on exchange: {exchange}")
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)

    def send(self, message: dict):
        body = json.dumps(message)
        self.channel.basic_publish(exchange=self.exchange, routing_key=self.queue, body=body)
        logger.debug("Message sent")

    def __del__(self):
        self.connection.close()
        logger.info("Connection closed")
