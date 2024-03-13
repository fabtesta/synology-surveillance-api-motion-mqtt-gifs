#!/usr/bin/env python3
import logging
import sqlite3
import sys
import time
from sqlite3 import Error

from handlers.camera_motion_event_handler import CameraMotionEventHandler
from services.config import parse_config
from services.syno_api import syno_cameras, syno_login

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

sql_create_processed_events_table = """ CREATE TABLE IF NOT EXISTS processed_events (
                                        id integer PRIMARY KEY,
                                        camera_id text NOT NULL,
                                        last_event_id int NOT NULL,
                                        processed_date timestamp NOT NULL
                                    ); """

sql_create_processed_events_table_unique = """ CREATE UNIQUE INDEX IF NOT EXISTS idx_processed_events_camera ON processed_events (camera_id); """


def create_connection(data_folder):
    try:
        conn = sqlite3.connect(data_folder + '/processed_events.db')
        print(sqlite3.version)
        return conn
    except Error as e:
        logging.error("CANNOT CREATE DB", e)

    return None


def create_processed_events_table(conn):
    try:
        c = conn.cursor()
        c.execute(sql_create_processed_events_table)
        c.execute(sql_create_processed_events_table_unique)
    except Error as e:
        logging.error("CANNOT CREATE TABLE", e)


def main():
    _, config_filename = sys.argv
    logging.info('Starting')
    logging.info('Parsing %s', config_filename)
    config = parse_config(config_filename)

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
    try:
        while True:
            time.sleep(10)
            cameras = syno_cameras(surveillance_station)
            for camera in cameras:
                logging.info('CameraMotionEventHandler  poll_event %s %s %s %s %s', camera['id'],
                             camera['newName'],
                             camera['model'], camera['vendor'], camera['ip'])
                camera_handler = CameraMotionEventHandler(processed_events_conn, camera,
                                                          config, surveillance_station)

                camera_handler.poll_event()

    except KeyboardInterrupt:
        logging.info('KeyboardInterrupt')

    logging.info('Ending')


if __name__ == "__main__":
    main()
