import datetime
import logging
from typing import List
from synology_api.surveillancestation import SurveillanceStation

from model.CameraConfig import CameraConfig
from services.mqtt_producer import MqttProducer
from services.syno_api import syno_camera_events, syno_recording_export
from services.video_converter import convert_video_gif


class CameraMotionEventHandler:
    def __init__(self, processed_events_conn, camera, config, surveillance_station: SurveillanceStation):
        self.camera = camera
        self.config = config
        self.camera_config: CameraConfig = __get_camera_config__(self.config['synology_cameras'], self.camera['id'])
        self.surveillance_station = surveillance_station
        self.mqtt_producer = MqttProducer(config=self.config)
        # Keep a FIFO of files processed so we can guard against duplicate
        # events
        self.processed_events_conn = processed_events_conn

    def poll_event(self):
        logging.info('Start getting last camera event for camera %s %s', self.camera_config.id,
                     self.camera_config.topic_name)
        now = datetime.datetime.now()
        today_midnight = datetime.datetime(now.year, now.month, now.day)
        camera_events = syno_camera_events(self.surveillance_station, self.camera_config.id, today_midnight)
        if camera_events.__len__() == 0:
            logging.info('No event found for date %s', today_midnight.strftime("%Y-%m-%d"))
            return

        camera_events_filtered = camera_events
        logging.info('Found %s events for camera %s %s', camera_events_filtered.__len__(), self.camera_config.id,
                     self.camera_config.topic_name)
        for camera_event in camera_events_filtered:
            logging.debug('Camera event %s - %s - %s - %s', camera_event['id'], camera_event['cameraId'],
                          camera_event['cameraName'],
                          camera_event['filePath'])
            if __check_already_processed_event_by_camera__(self.processed_events_conn, self.camera_config.id,
                                                           camera_event['id']):
                logging.info('Event %s from camera %s already processed', camera_event['id'],
                             camera_event['cameraId'])
                continue

            logging.info('Start downloading event video for event_id %s', camera_event['id'])
            mp4_file = syno_recording_export(self.surveillance_station, self.config["ffmpeg_working_folder"],
                                             camera_event['id'])
            outfile_gif = '{}/{}.gif'.format(self.config["ffmpeg_working_folder"], camera_event['id'])
            convert_retcode = convert_video_gif(self.camera_config.scale,
                                                self.camera_config.skip_first_n_secs,
                                                self.camera_config.max_length_secs,
                                                mp4_file, outfile_gif)
            if convert_retcode == 0:
                public_retcode = self.mqtt_producer.publish_gif_message(self.config['mqtt_gif_message_type'],
                                                                        '{}.gif'.format(camera_event['id']),
                                                                        outfile_gif, self.camera_config.topic_name)
                if public_retcode:
                    processed_event = (self.camera_config.id, camera_event['id'], datetime.datetime.now())
                    __replace_processed_events__(self.processed_events_conn, processed_event)
                    logging.info('Done processing event_id %i', camera_event['id'])
                else:
                    logging.error('Invalid return code from mqtt publish for event id %i camera topic %s',
                                  camera_event['id'],
                                  self.camera_config.topic_name)
            else:
                logging.error('Invalid return code from ffmpeg subprocess call for event id %i', camera_event['id'])


def __get_camera_config__(cameras_config, camera_id) -> CameraConfig:
    for camera_config in cameras_config:
        if camera_config["id"] == camera_id:
            return CameraConfig(**camera_config)
    return None


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
