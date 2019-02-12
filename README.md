# synology-surveillance-api-motion-mqtt-gifs
A python script to create animated gifs from videos recorded by cameras attached to Synology Surveillance Station inspired by similar project for [Ubiquiti Unifi camers](https://github.com/selfhostedhome/unifi-video-gif-mqtt) [(blog)](https://selfhostedhome.com/unifi-video-motion-detection-gif-notifications)

Supports DSM Surveillance APIs from version 2.

Supports multiple cameras polling and ffmpeg parameters

## Config File

Needs a simple JSON based config file passed in on the command line.

For example:

```json
{
  "mqtt_server": "broker.shiftr.io",
  "mqtt_port": 1883,
  "mqtt_user": "user",
  "mqtt_pwd": "password",
  "mqtt_base_topic": "synology/cameras/gifs",
  "ffmpeg_working_folder": "./gifs",
  "synology_base_api_url": "http://127.0.0.1",
  "synology_user": "admin",
  "synology_password": "password123",
  "synology_cameras": [
    {
      "id": 1, 
      "skip_first_n_secs": 5, //<-- Skip seconds recorded before motion event is triggered
      "max_length_secs": 5, //<-- Do not create gif for video full length but only with first n seconds
      "scale": 320, //<-- Determine quality and size of the output gif
      "topic_name": "camera_1" //<-- Configurable camera topic name
    },
    {
      "id": 2,
      "skip_first_n_secs": 7,
      "max_length_secs": 10,
      "scale": 640,
      "topic_name": "camera_2"
    }
  ]
}

```
* `mqtt_server`: MQTT server to publish notifications to
* `mqtt_port`: Port of MQTT server
* `mqtt_user`: Username of MQTT server
* `mqtt_pwd`: Password of MQTT server
* `mqtt_base_topic`: MQTT topic to publish new GIFs to.
* `ffmpeg_working_folder`: Working folder for downloaded mp4 videos and created GIFs
* `synology_base_api_url`: Base url of Synology Surveillance Station APIs
* `synology_user`: User to access Synology Surveillance Station APIs
* `synology_password`: User's password to access Synology Surveillance Station APIs
* `synology_cameras`: Array of cameras for events polling
    * `id`: Synology Surveillance Station camera id
    * `skip_first_n_secs`: Skip seconds recorded before motion event is triggered
    * `max_length_secs`: Do not create gif for video full length but only with first n seconds
    * `scale`: Determine quality and size of the output gif
    * `topic_name`: Configurable camera topic name that will be appended to the end of this base topic

If you don't know camera ids, leave cameras section empty and you'll get ids printed at first run
```
"synology_cameras": []
```
Example:
```
[INFO] (MainThread) Synology Info Camera Id 1 Name arzilla_veranda IP 192.168.1.87
[INFO] (MainThread) Synology Info Camera Id 2 Name arzilla_piazzale IP 192.168.1.88
[INFO] (MainThread) Synology Info Camera Id 3 Name arzilla_campo IP 192.168.1.148
[INFO] (MainThread) Synology Info Camera Id 4 Name arzilla_veranda_interno IP 192.168.1.126
```

## Installation

There is a docker image if you prefer to run using docker. For example:

```shell
docker run -v $(pwd)/config:/config \
    -v $(pwd)/gifs:/gifs \
    fabtesta/synology-surveillance-api-motion-mqtt-gifs:latest
```

or via docker compose.

```yaml
services:
  synology-surveillance-api-motion-mqtt-gifs:
    image: fabtesta/synology-surveillance-api-motion-mqtt-gifs:latest
    volumes:
      - ./config:/config
      - ./gifs:/gifs
    restart: unless-stopped
```

If you'd prefer to install dependencies yourself, you'll need:

* ffmpeg 4.0 (other versions probably work, but that's what I tested with)
* Python 3
* python libraries listed in `requirements.txt` (install via `pip install -r requirements.txt`)