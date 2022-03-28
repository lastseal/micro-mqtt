# -*- coding: utf-8 -*

from multiprocessing import Process
from . import config

import paho.mqtt.client as mqtt
import logging
import json
import time
import os

##
# MqttClient

class MqttClient:

    def __init__(self, host="mqtt.eclipse.org", port=1883, username=None, password=None):

        self.client = mqtt.Client()

        if username is not None and password is not None:
            self.client.username_pw_set(username, password)

        self.client.connect(host, port)
        self.client.on_log = self.on_log
        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect

        self.hadlers = {}

        self.loop = False

    def start(self):
        self.loop = True
        while self.loop:
            self.client.loop()
            time.sleep(0.01)

    def stop(self):
        self.loop = False

    def on_connect(self, client, userdata, level, buf):
        logging.debug("on_connect: %s", buf)

    def on_disconnect(self, client, userdata, rc):
        logging.debug("on_disconnect: %d", rc)
        if rc != 0:
            self.client.reconnect()         

    def on_log(self, client, userdata, level, buf):
        logging.debug("on_log: %s", buf)

    def on_publish(self, client, userdata, mid):
        logging.debug("on_publish: ok")

    def publish(self, topic, data):
        res = self.client.publish(topic, json.dumps(data))
        logging.debug("publish response: %s", res)

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    def subscribe(self, topic, handle):
        
        try:
            def on_message(client, userdata, message):

                if message.topic in self.hadlers:
                    payload = str(message.payload, 'utf-8')
                    logging.debug("received: [%s] %s", message.topic, payload)
                    self.hadlers[message.topic](
                        json.loads(payload), 
                        message.topic
                    )

            self.hadlers[topic] = handle

            self.client.on_message = on_message
            self.client.subscribe(topic)

        except Exception as ex:
            logging.error(ex)
            raise ex

##
# SubscriberServer

class SubscriberServer:

    def __init__(self, host="mqtt.eclipse.org", port=1883, username=None, password=None):

        self.client = MqttClient(host, port, username, password)

        self.process = None
        self.config = []

    def __del__(self):
        if self.process is not None:
            self.process.join()

    def __target__(self):
        for c in self.config:
            self.client.subscribe(c["topic"], c["handle"])
        self.client.start()

    def start(self, topic, handle):

        if self.process is not None:
            for c in self.config:
                self.client.unsubscribe(c["topic"])
            self.process.terminate()

        self.config.append({"topic":topic, "handle":handle})

        self.process = Process(target=self.__target__)
        self.process.start()

##
# RpcServer

class RpcServer(SubscriberServer):

    def __target__(self):

        self.handles = {}

        for c in self.config:
            
            def response(data, topic):
                if topic in self.handles:
                    self.client.publish(f"{topic}/res", {
                        "result": self.handles[topic](data)
                    })

            command = c["topic"]
            self.handles[command] = c["handle"]
            self.client.subscribe(command, response)

        self.client.start()
        
##
# Singleton

MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT") or "1883")

__singleton__ = MqttClient(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS)
__subscriber__ = SubscriberServer(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS)
__rpc__ = RpcServer(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS)

def subscribe(topic):
    def decorator(handle):
        __subscriber__.start(topic, handle)
        
    return decorator

def publish(topic, data):
    __singleton__.publish(topic, data)

def rpc(command):
    def decorator(handle):
        __rpc__.start(command, handle)
        
    return decorator

def call(command, data=None):

    __result__ = {}

    def handle(data, topic):
        __result__['result'] = data
        __singleton__.stop()

    __singleton__.subscribe(f"{command}/res", handle)
    __singleton__.publish(command, {} if data is None else data)
    __singleton__.start()
    __singleton__.unsubscribe(f"{command}/res")
        
    return __result__['result']
