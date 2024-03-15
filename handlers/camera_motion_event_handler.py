import datetime
import logging
from typing import List
from synology_api.surveillancestation import SurveillanceStation

from model.CameraConfig import CameraConfig
from services.db_utils import check_already_processed_event_by_camera, replace_processed_events
from services.mqtt_producer import MqttProducer
from services.syno_api import syno_camera_events, syno_recording_export, syno_camera_snapshot
from services.video_converter import convert_video_gif


class CameraMotionEventHandler:
    def __init__(self, processed_events_conn, camera, camera_config: CameraConfig, mqtt_producer: MqttProducer,
                 surveillance_station: SurveillanceStation, working_folder: str):
        self.camera = camera
        self.camera_config = camera_config
        self.surveillance_station = surveillance_station
        self.mqtt_producer = mqtt_producer
        self.working_folder = working_folder
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
            if check_already_processed_event_by_camera(self.processed_events_conn, self.camera_config.id,
                                                       camera_event['id']):
                logging.info('Event %s from camera %s already processed', camera_event['id'],
                             camera_event['cameraId'])
                continue

            logging.info('Start downloading event video for event_id %s', camera_event['id'])
            mp4_file = syno_recording_export(self.surveillance_station, self.working_folder,
                                             camera_event['id'])
            outfile_gif = '{}/{}.gif'.format(self.working_folder, camera_event['id'])
            convert_retcode = convert_video_gif(self.camera_config.scale,
                                                self.camera_config.skip_first_n_secs,
                                                self.camera_config.max_length_secs,
                                                mp4_file, outfile_gif)
            if convert_retcode == 0:
                public_retcode = self.mqtt_producer.publish_file_message(self.camera_config.mqtt_message_type,
                                                                         '{}.gif'.format(camera_event['id']),
                                                                         outfile_gif, self.camera_config.topic_name)
                if public_retcode:
                    processed_event = (self.camera_config.id, camera_event['id'], datetime.datetime.now())
                    replace_processed_events(self.processed_events_conn, processed_event)
                    logging.info('Done processing event_id %i', camera_event['id'])
                else:
                    logging.error('Invalid return code from mqtt publish for event id %i camera topic %s',
                                  camera_event['id'],
                                  self.camera_config.topic_name)
            else:
                logging.error('Invalid return code from ffmpeg subprocess call for event id %i', camera_event['id'])

    def snap_camera(self):
        logging.info('Getting camera snap for camera %s %s', self.camera_config.id,
                     self.camera_config.topic_name)
        outfile_jpg = syno_camera_snapshot(self.surveillance_station, self.working_folder, self.camera_config.id)
        public_retcode = self.mqtt_producer.publish_file_message(self.camera_config.mqtt_message_type,
                                                                 '{}.jpg'.format(self.camera_config.id),
                                                                 outfile_jpg, self.camera_config.topic_name)
        if public_retcode:
            logging.info('Done processing snapshot %i', self.camera_config.id)
        else:
            logging.error('Invalid return code from mqtt publish for camera id %i camera topic %s',
                          self.camera_config.id,
                          self.camera_config.topic_name)
