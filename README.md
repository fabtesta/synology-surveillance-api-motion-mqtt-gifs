# synology-surveillance-api-motion-mqtt-gifs
A python script to create animated gifs and snapshots from videos recorded by cameras attached to Synology Surveillance Station inspired by similar project for [Ubiquiti Unifi camers](https://github.com/selfhostedhome/unifi-video-gif-mqtt) [(blog)](https://selfhostedhome.com/unifi-video-motion-detection-gif-notifications)

_Status_\
![maintained - yes](https://img.shields.io/badge/maintained-yes-blue)

_New version_\
[![v 3.0.0 - breaking changes](https://img.shields.io/badge/v_3.0.0-breaking_changes-important)](https://github.com/N4S4/synology-api)

_Many thanks to N4S4 and Synology API wrapper library_\
[![please star - synology-api](https://img.shields.io/badge/please_star-synology--api-2ea44f)](https://github.com/N4S4/synology-api)

Supports [Synology DSM APIs version 7](https://global.download.synology.com/download/Document/Software/DeveloperGuide/Os/DSM/All/enu/DSM_Login_Web_API_Guide_enu.pdf)\
Supports [Synology Surveillance APIs version 2](https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/SurveillanceStation/All/enu/Surveillance_Station_Web_API.pdf)

Supports multiple cameras polling and ffmpeg parameters
Remembers already processed events across restarts.


## This docker image has passed 30k downloads on Docker Hub!
<a href="https://www.buymeacoffee.com/fabtesta" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/lato-blue.png" alt="Buy Me A Coffee" style="height: 51px !important;width: 217px !important;" ></a>

## Config File

Needs a simple JSON based config file passed in on the command line.

For example:

```json
{
  "data_folder": "./data", // <-- Leave it empty if you are using docker image or set the bind mount to volume /data
  "polling_time": 60,
  "mqtt_server": "broker.shiftr.io",
  "mqtt_port": 1883,
  "mqtt_user": "user",
  "mqtt_pwd": "password",
  "mqtt_base_topic": "synology/cameras/gifs",
  "ffmpeg_working_folder": "./gifs", // <-- Leave it empty if you are using docker image or set the bind mount to volume /gifs
  "synology_ip": "127.0.0.1",
  "synology_port": "5001",
  "synology_user": "admin",
  "synology_password": "password123",
  "synology_cameras": [
    {
      //CAMERA GIF TO LOCAL FILE
      "id": 1,
      "mqtt_message_type": "localfile", // <-- or base64 if you want to publish the file encode to base64
      "mode": "gif", // <-- or snapshot if you want to snap a frame from the motion event
      "skip_first_n_secs": 5,
      "max_length_secs": 5,
      "scale": 320,
      "topic_name": "camera_1"
    },
    {
      //CAMERA GIF TO BASE64
      "id": 2,
      "mqtt_message_type": "base64", // <-- or localfile if you want to publish the file name saved under 'ffmpeg_working_folder'
      "mode": "gif", // <-- or snapshot if you want to snap a frame from the motion event
      "skip_first_n_secs": 7,
      "max_length_secs": 10,
      "scale": 640,
      "topic_name": "camera_2"
    },
    {
      //CAMERA SNAP ONLY TO BASE64
      "id": 3,
      "mqtt_message_type": "base64", // <-- or localfile if you want to publish the file name saved under 'ffmpeg_working_folder'
      "mode": "snap",
      "scale": 640,
      "topic_name": "camera_3"
    }
  ]
}

```
* `data_folder`: Path where to stored sqlite db for already processed events (preserve state across restarts). Leave empty if using docker image.
* `polling_time`: Polling cycle in seconds
* `mqtt_server`: MQTT server to publish notifications to
* `mqtt_port`: Port of MQTT server
* `mqtt_user`: Username of MQTT server
* `mqtt_pwd`: Password of MQTT server
* `mqtt_base_topic`: MQTT topic to publish new GIFs to.
* `ffmpeg_working_folder`: Working folder for downloaded mp4 videos and created GIFs
* `synology_ip`: Host IP where Synology Surveillance Station APIs are exposed
* `synology_port`: Host port where Synology Surveillance Station APIs are exposed
* `synology_user`: User to access Synology Surveillance Station APIs
* `synology_password`: User's password to access Synology Surveillance Station APIs
* `synology_cameras`: Array of cameras for events polling
    * `id`: Synology Surveillance Station camera id
    * `mqtt_message_type`:
      * `localfile`: publish the file name saved under 'ffmpeg_working_folder'
      * `base64`: publish the file encoded to base64
      
    * `mode`:
      * `gif`: exports the video event and converts it in a gif with the following options:
        * `skip_first_n_secs`
        * `max_length_secs`
        * `scale`
      * `snap`: publish the file encoded to base64 with the following options:
        * `scale`
    * `skip_first_n_secs`: Skip seconds recorded before motion event is triggered
    * `max_length_secs`: Do not create gif for video full length but only with first n seconds
    * `scale`: Determine quality and size of the output gif/snap
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
docker run \
    -v $(pwd)/config:/config \
    -v $(pwd)/data:/data \
    -v $(pwd)/gifs:/gifs \
    fabtesta/synology-surveillance-api-motion-mqtt-gifs:latest
```

or via docker compose.
######(bind-mount)
```yaml
services:
  synology-surveillance-api-motion-mqtt-gifs:
    image: fabtesta/synology-surveillance-api-motion-mqtt-gifs:latest
    volumes:
      - ./config:/config
      - ./data:/data
      - ./gifs:/gifs
    restart: unless-stopped
```
######(persistent volume)
```yaml - 
services:
  synology-surveillance-api-motion-mqtt-gifs:
    image: fabtesta/synology-surveillance-api-motion-mqtt-gifs:latest
    volumes:
      - ./config:/config
      - syno_data:/data
      - ./gifs:/gifs
    restart: unless-stopped
    
volumes:
  syno_data:
```

If you'd prefer to install dependencies yourself, you'll need:

* ffmpeg 4.4 (other versions probably work, but that's what I tested with)
* Python 3.9
* python libraries listed in `requirements.txt` (install via `pip install -r requirements.txt`)