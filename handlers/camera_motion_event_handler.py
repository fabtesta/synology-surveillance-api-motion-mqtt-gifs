import base64
import datetime
import logging
from typing import List

import paho.mqtt.client as mqtt
from PIL import Image
from paho.mqtt.enums import CallbackAPIVersion
from synology_api.surveillancestation import SurveillanceStation

from services.syno_api import syno_camera_events, syno_recording_export
from services.video_converter import convert_video_gif


class CameraMotionEventHandler:
    def __init__(self, processed_events_conn, camera, config, surveillance_station: SurveillanceStation):
        self.camera = camera
        self.config = config
        self.camera_config = __get_camera_config__(self.config['synology_cameras'], self.camera['id'])
        self.surveillance_station = surveillance_station
        self.mqtt_client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.mqtt_client.username_pw_set(username=self.config["mqtt_user"], password=self.config["mqtt_pwd"])
        # Keep a FIFO of files processed so we can guard against duplicate
        # events
        self.processed_events_conn = processed_events_conn

    def __gif_as_base64__(self, file_path):
        with open(file_path, "rb") as f:
            # Open the GIF file
            img = Image.open(f)
            # Convert the image to bytes
            img_bytes = img.tobytes()
            # Encode the bytes as base64
            base64_data = base64.b64encode(img_bytes).decode("utf-8")
        return base64_data

    def publish_mqtt_message(self, gif):
        logging.info('publish_mqtt_message gif %s mqtt_server %s mqtt_port %i mqtt_base_topic %s topic_name %s',
                     gif, self.config["mqtt_server"], self.config["mqtt_port"], self.config["mqtt_base_topic"],
                     self.camera_config["topic_name"])

        self.mqtt_client.connect(self.config["mqtt_server"],
                                 self.config["mqtt_port"])
        retcode = self.mqtt_client.publish(
            self.config["mqtt_base_topic"] + "/" + self.camera_config["topic_name"], gif)
        return retcode

    def poll_event(self):
        logging.info('Start getting last camera event for camera %s %s', self.camera_config["id"],
                     self.camera_config["topic_name"])
        now = datetime.datetime.now()
        today_midnight = datetime.datetime(now.year, now.month, now.day)
        camera_events = syno_camera_events(self.surveillance_station, self.camera_config['id'], today_midnight)
        if camera_events.__len__() == 0:
            logging.info('No event found for date %s', today_midnight.strftime("%Y-%m-%d"))
            return

        # camera_events_filtered = __get_camera_events_filtered__(camera_events, self.camera_config['id'])
        # if camera_events_filtered.__len__() == 0:
        #     logging.info('No event found for camera %s %s', self.camera_config["id"],
        #                  self.camera_config["topic_name"])
        #     return
        camera_events_filtered = camera_events
        logging.info('Found %s events for camera %s %s', camera_events_filtered.__len__(), self.camera_config["id"],
                     self.camera_config["topic_name"])
        for camera_event in camera_events_filtered:
            logging.debug('Camera event %s - %s - %s - %s', camera_event['id'], camera_event['cameraId'],
                         camera_event['cameraName'],
                         camera_event['filePath'])
            if __check_already_processed_event_by_camera__(self.processed_events_conn, self.camera_config["id"],
                                                           camera_event['id']):
                logging.info('Event %s from camera %s already processed', camera_event['id'],
                             camera_event['cameraId'])
                continue

            logging.info('Start downloading event video for event_id %s', camera_event['id'])
            mp4_file = syno_recording_export(self.surveillance_station, self.config["ffmpeg_working_folder"],
                                             camera_event['id'])
            outfile_gif = '{}/{}.gif'.format(self.config["ffmpeg_working_folder"], camera_event['id'])
            convert_retcode = convert_video_gif(self.camera_config["scale"],
                                                self.camera_config["skip_first_n_secs"],
                                                self.camera_config["max_length_secs"],
                                                mp4_file, outfile_gif)
            if convert_retcode == 0:
                gif = None
                if self.config['mqtt_gif_message_type'] == 'base64':
                    gif = self.__gif_as_base64__(outfile_gif)
                else:
                    gif = '{}.gif'.format(camera_event['id'])
                public_retcode = self.publish_mqtt_message(gif)
                if public_retcode:
                    processed_event = (self.camera_config["id"], camera_event['id'], datetime.datetime.now())
                    __replace_processed_events__(self.processed_events_conn, processed_event)
                    logging.info('Done processing event_id %i', camera_event['id'])
                else:
                    logging.error('Invalid return code from mqtt publish for event id %i camera topic %s',
                                  camera_event['id'],
                                  self.camera_config["topic_name"])
            else:
                logging.error('Invalid return code from ffmpeg subprocess call for event id %i', camera_event['id'])


def __get_camera_config__(cameras_config, camera_id) -> dict:
    for camera_config in cameras_config:
        if camera_config["id"] == camera_id:
            return camera_config
    return {}


def __get_camera_events_filtered__(camera_events, camera_id) -> List[dict]:
    camera_events_filtered: List[dict] = []
    for camera_event in camera_events:
        if camera_event["cameraId"] == camera_id:
            camera_events_filtered.append(camera_event)
    return camera_events_filtered


def __check_already_processed_event_by_camera__(conn, camera_id, event_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM processed_events WHERE camera_id=? AND last_event_id >=?", (camera_id, event_id))

    rows = cur.fetchall()

    already_processed = False
    for row in rows:
        logging.error("Event %s already processed %s", event_id, row)
        already_processed = True

    return already_processed


def __replace_processed_events__(conn, processed_event):
    sql = ''' REPLACE INTO processed_events(camera_id, last_event_id ,processed_date)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, processed_event)

    conn.commit()
    return cur.lastrowid
