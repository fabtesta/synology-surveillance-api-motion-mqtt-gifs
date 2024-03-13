#FROM jrottenberg/ffmpeg:4.4-alpine
FROM python:3.9.13-alpine

WORKDIR /app
ADD ./handlers ./handlers
ADD ./services ./services
ADD synology_surveillance_motion_mqtt_gifs.py .
ADD requirements.txt .
VOLUME /config
VOLUME /gifs
VOLUME /data

ENV PATH /usr/local/bin:$PATH
ENV LANG C.UTF-8

RUN apk add --no-cache ca-certificates
RUN apk add --update --no-cache ffmpeg
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install -r requirements.txt

ENTRYPOINT ["/usr/bin/env"]
CMD ["python3", "/app/synology_surveillance_motion_mqtt_gifs.py", "/config/config.json"]
