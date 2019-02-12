FROM jrottenberg/ffmpeg:4.0

ADD synology_surveillance_motion_mqtt_gifs.py requirements.txt /
VOLUME /config

RUN apt-get update && \
  apt-get install -y python3 python3-pip && \
  pip3 install -r /requirements.txt \
  && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/usr/bin/env"]
CMD ["python3", "/synology_surveillance_motion_mqtt_gifs.py", "/config/config.json"]
