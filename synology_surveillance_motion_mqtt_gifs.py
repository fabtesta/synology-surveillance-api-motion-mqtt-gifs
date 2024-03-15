#!/usr/bin/env python3
import logging
import sys
import time

from handlers.camera_motion_event_handler import CameraMotionEventHandler
from model.CameraConfig import CameraConfig
from services.config_utils import parse_config, get_camera_config
from services.db_utils import create_connection, create_processed_events_table
from services.mqtt_producer import MqttProducer
from services.syno_api import syno_cameras, syno_login

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def main():
    _, config_filename = sys.argv
    logging.info('Starting')
    logging.info('Parsing %s', config_filename)
    config = parse_config(config_filename)
    logging.info('Polling every %s seconds', config['polling_time'])

    config_data_folder = ''
    if 'data_folder' in config:
        config_data_folder = config["data_folder"]
    if config_data_folder == '':
        config_data_folder = "/data"

    logging.info('Creating/Opening processed_events database on file %s', config_data_folder)
    processed_events_conn = create_connection(config_data_folder)
    if processed_events_conn is not None:
        # create processed_events table
        create_processed_events_table(processed_events_conn)
    else:
        logging.error('Error! cannot create the database connection.')
        return

    surveillance_station = syno_login(config["synology_ip"], config["synology_port"],
                                      config["synology_user"],
                                      config["synology_password"])
    if surveillance_station is None:
        logging.error('Synology credentials not valid')
        exit(-1)

    logging.info('Synology Auth ok %s', surveillance_station.session.sid)
    mqtt_producer = MqttProducer(config=config)
    try:
        while True:
            time.sleep(int(config['polling_time']))
            cameras = syno_cameras(surveillance_station)
            for camera in cameras:
                logging.info('CameraMotionEventHandler  poll_event %s %s %s %s %s', camera['id'],
                             camera['newName'],
                             camera['model'], camera['vendor'], camera['ip'])
                camera_config: CameraConfig = get_camera_config(config['synology_cameras'],
                                                                camera['id'])
                camera_handler = CameraMotionEventHandler(processed_events_conn, camera,
                                                          camera_config=camera_config, mqtt_producer=mqtt_producer,
                                                          surveillance_station=surveillance_station,
                                                          working_folder=config["ffmpeg_working_folder"])

                if camera_config is None:
                    continue
                if camera_config.mode.lower() == 'gif':
                    camera_handler.poll_event()
                elif camera_config.mode.lower() == 'snap':
                    camera_handler.snap_camera()

    except KeyboardInterrupt:
        logging.info('KeyboardInterrupt')

    logging.info('Ending')


if __name__ == "__main__":
    main()
