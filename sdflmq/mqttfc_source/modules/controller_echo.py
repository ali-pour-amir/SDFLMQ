import paho.mqtt.client as mqtt
import threading
import time

channels_to_subscribe = ['client_intro', 'echo']

def on_connect(client,userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("client_intro")

def on_message(client,userdata, msg):
    print(msg.payload.decode())

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect("broker.emqx.io",1883,60)


