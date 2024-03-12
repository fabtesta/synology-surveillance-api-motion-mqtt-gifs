import configparser
import datetime
from unittest import TestCase

from synology_api.surveillancestation import SurveillanceStation

from services.config import parse_config
from services.syno_api import syno_login, syno_cameras, syno_camera_events, syno_recording_export


class TestSynoApi(TestCase):
    config: dict[str, str]
    ss: SurveillanceStation

    def setUp(self):
        self.config = parse_config('./resources/config-test.json')
        self.ss = syno_login(self.config["synology_ip"], self.config["synology_port"], self.config["synology_user"],
                             self.config["synology_password"])

    def test_syno_login(self):
        self.assertIsNotNone(self.ss)
        self.assertEqual(self.ss.base_url, self.config["synology_base_api_url"])
        self.assertIsNotNone(self.ss.session)
        self.assertIsNotNone(self.ss.session.sid)
        self.assertIsNot(self.ss.session.sid, '')
        ss_info = self.ss.surveillance_station_info()
        self.assertIsNotNone(ss_info)
        ss_info_data = ss_info['data']
        self.assertIsNotNone(ss_info_data)
        #  self.assertEqual(ss_info_data['hostname'], self.config["hostname"])
        self.assertEqual(ss_info_data['path'], '/webman/3rdparty/SurveillanceStation/')

    def test_syno_cameras(self):
        cameras = syno_cameras(self.ss)
        self.assertIsNotNone(cameras)
        self.assertEqual(cameras.__len__(), 5)

    def test_syno_camera_events(self):
        events = syno_camera_events(self.ss, datetime.datetime(2024, 3, 12))
        self.assertIsNotNone(events)
        self.assertEqual(events.__len__(), 100)

    def test_syno_recording_export(self):
        recording = syno_recording_export(self.ss, self.config["ffmpeg_working_folder"], 738562)
        self.assertIsNotNone(recording)
        self.assertEqual(recording, './resources/gifs/738562.mp4')
