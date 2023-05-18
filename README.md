# Micro MQTT
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Instalación

```bash
pip install git+https://github.com/lastseal/micro-mqtt
```

## Uso Básico

Microservicio MQTT PubSub

```python
from micro import mqtt

@mqtt.subscribe("topic")
def topic1(data, topic):
    print(data)
```

```python
from micro import mqtt

mqtt.publish("topic", {"data": "topic 1"})
```

Microservicio MQTT RPC

```python
from micro import mqtt

@mqtt.rpc("status")
def status(data):
    return "status"
```

```python
from micro import mqtt

res = mqtt.call("status")
print(res)
```
