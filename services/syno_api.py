from synology_api import surveillancestation


def syno_login(base_url, user, password) -> dict[str, object] | str:
    ss = surveillancestation.SurveillanceStation(ip_address='192.168.1.27', port='5001', username='hass',
                                                 password='Password')

    camera_list = ss.camera_list()

    return camera_list
