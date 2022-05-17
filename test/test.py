import sys
sys.path.append('./micro')
import mqtt
import time

def test_1():

    @mqtt.subscribe("micro.mqtt.sub_1")
    def sub_1(data):
        print(data)

    time.sleep(0.5)
    mqtt.publish("micro.mqtt.sub_1", "test")
    time.sleep(2)

    assert True

def test_2():

    @mqtt.subscribe("micro.mqtt.sub_1")
    def sub_1(data):
        print(data)

    @mqtt.subscribe("micro.mqtt.sub_1")
    def sub_2(data):
        print(data)

    time.sleep(0.5)
    mqtt.publish("micro.mqtt.sub_1", "test")
    time.sleep(2)

    assert True

def test_3():

    @mqtt.rpc("micro.mqtt.test_1")
    def rpc_1(query):
        print("query", query)
        return query

    time.sleep(0.5)

    res = mqtt.call("micro.mqtt.test_1", "test_1")
    assert res == "test_1"
