import json
from aio_pika import connect_robust, Message, DeliveryMode
from fastapi.encoders import jsonable_encoder
from .base import AbstractLogQueue
from settings import settings


class RabbitMQLogQueue(AbstractLogQueue):
    def __init__(
        self,
        url: str = settings.MQ_URL,  # "amqp://admin:admin123@rabbitmq/"
        queue_name: str = settings.QUEUE_NAME,  # "log_queue"
    ):
        self.url = url
        self.queue_name = queue_name

    async def enqueue(self, log_data: dict):
        log_data = jsonable_encoder(log_data)
        connection = await connect_robust(self.url)
       
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.queue_name, durable=True)

            await channel.default_exchange.publish(
                Message(
                    body=json.dumps(log_data).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=queue.name,
            )
