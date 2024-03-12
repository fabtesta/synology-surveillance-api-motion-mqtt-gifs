#!/usr/bin/env python3

import logging
import sys
import time
from collections import deque

from handlers.camera_motion_event_handler import CameraMotionEventHandler
from services.config import parse_config
from services.syno_api import syno_login, syno_cameras

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def syno_info(param, sid):
    pass


def main():
    _, config_filename = sys.argv
    logging.info('Starting')
    logging.info('Parsing %s', config_filename)
    config = parse_config(config_filename)

    processed_events = deque(maxlen=100)
    logged_in = False
    try:
        while True:
            time.sleep(10)
            if not logged_in:
                surveillance_station = syno_login(config["synology_ip"], config["synology_port"],
                                                  config["synology_user"],
                                                  config["synology_password"])
                if surveillance_station is None:
                    logging.error('Synology credentials not valid')
                    continue
                else:
                    logged_in = True
                    logging.info('Synology Auth ok %s', surveillance_station.session.sid)
                    cameras = syno_cameras(surveillance_station)
                    for camera in cameras:
                        logging.info('CameraMotionEventHandler  poll_event %s %s %s %s %s', camera['id'],
                                     camera['newName'],
                                     camera['model'], camera['vendor'], camera['ip'])
                        camera_handler = CameraMotionEventHandler(processed_events, camera,
                                                                  config, surveillance_station)

                        camera_handler.poll_event()

    except KeyboardInterrupt:
        logging.info('KeyboardInterrupt')

    logging.info('Ending')


if __name__ == "__main__":
    main()
