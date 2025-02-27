#!/usr/bin/env python3
import asyncio
import email
import logging
import os
import json
import re
import signal
import time
from datetime import datetime
from email.policy import default
from unittest import case
from weakref import KeyedRef

from aiosmtpd.controller import Controller
from paho.mqtt import publish


defaults = {
    "SMTP_PORT": 1025,
    "MQTT_HOST": "localhost",
    "MQTT_PORT": 1883,
    "MQTT_USERNAME": "",
    "MQTT_PASSWORD": "",
    "MQTT_TOPIC": "mqtt",
    "MQTT_RESET_TIME": "300",
    "MQTT_RESET_PAYLOAD": "OFF",
    "SAVE_ATTACHMENTS": "True",
    "SAVE_ATTACHMENTS_DURING_RESET_TIME": "False",
    "SAVE_ATTACHMENTS_DIR": "/attachments",
    "DEBUG": "False",
}
config = {
    setting: os.environ.get(setting, default) for setting, default in defaults.items()
}
# Boolify
for key, value in config.items():
    if value == "True":
        config[key] = True
    elif value == "False":
        config[key] = False

level = logging.DEBUG if config["DEBUG"] else logging.INFO

log = logging.getLogger("mailqtt")
log.setLevel(level)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Log to console
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)


class MailQTTHandler:
    def __init__(self, loop):
        self.loop = loop
        self.reset_time = int(config["MQTT_RESET_TIME"])
        self.handles = {}
        self.quit = False
        signal.signal(signal.SIGTERM, self.set_quit)
        signal.signal(signal.SIGINT, self.set_quit)
        if config["SAVE_ATTACHMENTS"]:
            log.info("Configured to save attachments")

    def prep_msg(self, msg):
        try:
            subject = msg['Subject']
            cam_match = re.compile('Person Detected from (.*) at')
            thing_match = re.compile('(.*) Detected from')
        except KeyError as e:
            raise e("Malformed message. Is this testing?")
        camera = cam_match.search(subject).group(1)
        detected_thing = thing_match.search(subject).group(1)

        return camera, detected_thing, detected_thing.lower()

    async def handle_DATA(self, server, session, envelope):
        log.debug("Message from %s", envelope.mail_from)
        msg = email.message_from_bytes(envelope.original_content, policy=default)
        decoded_msg = envelope.content.decode("utf8", errors="replace")
        
        log.debug(
            "Message data (truncated): %s",
            decoded_msg[:350],
        )
        camera, detected_thing, topic_suffix = self.prep_msg(msg)
        topic = config["MQTT_TOPIC"] + "/" + topic_suffix
        
        payload = {
            "subject": msg['Subject'],
            "camera": camera,
            "detected_thing": detected_thing
        }

        # Save attached files if configured to do so.
        if config["SAVE_ATTACHMENTS"] and (
            # Don't save them during reset time unless configured to do so.
            topic not in self.handles
            or config["SAVE_ATTACHMENTS_DURING_RESET_TIME"]
        ):
            log.debug(
                'Saving attachments. Topic "%s" already triggered: %s, '
                "Save attachment override: %s",
                topic,
                topic in self.handles,
                config["SAVE_ATTACHMENTS_DURING_RESET_TIME"],
            )
            for att in msg.iter_attachments():
                # Just save images
                if not att.get_content_type().startswith("image"):
                    continue
                filename = att.get_filename()
                image_data = att.get_content()
                full_filename= camera + "-" + filename
                file_path = os.path.join(config["SAVE_ATTACHMENTS_DIR"] + "/", full_filename)
                log.info("Saving attached file %s to %s", filename, file_path)
                payload["filename"] = full_filename
                with open(file_path, "wb") as f:
                    f.write(image_data)
        else:
            log.debug("Not saving attachments")
            log.debug(self.handles)
        
        self.mqtt_publish(topic, json.dumps(payload))

        # Cancel any current scheduled resets of this topic
        if topic in self.handles:
            self.handles.pop(topic).cancel()

        if self.reset_time:
            # Schedule a reset of this topic
            self.handles[topic] = self.loop.call_later(
                self.reset_time, self.reset, topic
            )
        return "250 Message accepted for delivery"

    def mqtt_publish(self, topic, payload):
        log.info('Publishing "%s" to %s', payload, topic)
        try:
            publish.single(
                topic,
                payload,
                hostname=config["MQTT_HOST"],
                port=int(config["MQTT_PORT"]),
                auth={
                    "username": config["MQTT_USERNAME"],
                    "password": config["MQTT_PASSWORD"],
                }
                if config["MQTT_USERNAME"]
                else None,
            )
        except Exception as e:
            log.exception("Failed publishing")

    def reset(self, topic):
        log.info(f"Resetting topic {topic}")
        self.handles.pop(topic)
        self.mqtt_publish(topic, config["MQTT_RESET_PAYLOAD"])

    def set_quit(self, *args):
        log.info("Quitting...")
        self.quit = True


if __name__ == "__main__":
    log.debug(", ".join([f"{k}={v}" for k, v in config.items()]))

    loop = asyncio.get_event_loop()
    c = Controller(
        handler=MailQTTHandler(loop),
        loop=loop,
        hostname="0.0.0.0",
        port=config["SMTP_PORT"],
    )
    c.start()
    log.info("Running")
    try:
        while not c.handler.quit:
            time.sleep(0.5)
        c.stop()
    except:
        c.stop()
        raise
