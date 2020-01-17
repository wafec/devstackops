import pika
import os


credentials = pika.PlainCredentials(os.environ["RABBIT_USER"], os.environ["RABBIT_PASS"])
parameters = pika.ConnectionParameters(
    os.environ["RABBIT_HOST"],
    os.environ["RABBIT_PORT"],
    os.environ["RABBIT_VHOST"],
    credentials
)
connection = pika.BlockingConnection(parameters=parameters)
channel = connection.channel()