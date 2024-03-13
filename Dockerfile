FROM jrottenberg/ffmpeg:4.1-alpine

ADD synology_surveillance_motion_mqtt_gifs.py requirements.txt /
VOLUME /config
VOLUME /gifs
VOLUME /data

ENV PATH /usr/local/bin:$PATH
ENV LANG C.UTF-8

RUN apk add --no-cache ca-certificates

ENV PYTHON_VERSION 3.9.13

# Install python/pip
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install -r /requirements.txt

ENTRYPOINT ["/usr/bin/env"]
CMD ["python3", "/synology_surveillance_motion_mqtt_gifs.py", "/config/config.json"]
