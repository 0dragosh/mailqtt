# mailqtt

Receive emails via SMTP and publish to MQTT.

My usecase is a standard way of fetching events out of IP cameras that don't support ONVIF events, Reolink, in particular.

## Run it

1. Create venv and activate it.

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
2022-05-20 18:16:19,123 - root - INFO - Running
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

