# mailqtt

Receive emails and publish to MQTT. Super simple stuff. Topic will be `<configurable_prefix>/<sender_email.replace('@', '')>`.

I needed this to make my D-Link camera's motion sensor functionality useful.
Available actions on the camera are to send an email or upload an image to an FTP..
This script makes it easier to integrate into automation systems.

It's based on aiosmtpd and paho-mqtt.

## Run it

1. Create venv and activate it. Or don't.

1. `pip install -r requirements.txt`.

1. Give it some env vars. These are the defaults so omit whatever looks good.
   * SMTP_PORT=1025
   * MQTT_HOST=localhost
   * MQTT_PORT=1883
   * MQTT_USERNAME=""
   * MQTT_PASSWORD=""
   * MQTT_TOPIC=mailqtt
   * MQTT_RESET_TIME=300
   * MQTT_RESET_PAYLOAD=OFF
   * SAVE_ATTACHMENTS=True
   * SAVE_ATTACHMENTS_DURING_RESET_TIME=False
   * ATTACHMENTS_DIR=/attachments
   * DEBUG=False

1. Go.
```
$ python mailqtt.py
2017-11-08 22:36:27,658 - root - INFO - Running
```

## Run it in docker

```
$ docker build -t mailqtt .
$ docker run -d \
    --name mailqtt \
    --net host \
    --restart always \
    -e "MQTT_USERNAME=mqtt" \
    -e "MQTT_PASSWORD=mqtt" \
    -e "DEBUG=True" \
    -v /etc/localtime:/etc/localtime:ro \
    -v $PWD/log:/mailqtt/log \
    -v $PWD/attachments:/mailqtt/attachments \
    mailqtt
```

