import logging
import sqlite3
from sqlite3 import Error

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


def check_already_processed_event_by_camera(conn, camera_id, event_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM processed_events WHERE camera_id=? AND last_event_id >=?", (camera_id, event_id))

    rows = cur.fetchall()

    already_processed = False
    for row in rows:
        logging.error("Event %s already processed %s", event_id, row)
        already_processed = True

    return already_processed


def replace_processed_events(conn, processed_event):
    sql = ''' REPLACE INTO processed_events(camera_id, last_event_id ,processed_date)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, processed_event)

    conn.commit()
    return cur.lastrowid
