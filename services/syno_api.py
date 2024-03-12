import json
import logging
import sys
from datetime import datetime

from synology_api.surveillancestation import SurveillanceStation

# SYNO.API urls
synoApiLoginUrl = "{}/webapi/entry.cgi?api=SYNO.API.Auth&method=login&version=7" \
                  "&session=SurveillanceStation&enable_syno_token=yes&account={}&passwd={}"
synoApiCamerasInfoUrl = "{}/webapi/entry.cgi?api=SYNO.SurveillanceStation.Camera&method=List&version=1&_sid={}"
synoApiEventQueryUrl = "{}/webapi/entry.cgi?api=SYNO.SurveillanceStation.Event&method=List" \
                       "&version=4&locked=0&reason=2&limit=1&cameraIds={}&_sid={}"
synoApiEventDownloadUrl = "{}/webapi/entry.cgi?api=SYNO.SurveillanceStation.Event" \
                          "&method=Download&version=4&analyevent=false&mountId=0" \
                          "&eventId={}&_sid={}"


def syno_login(ip, port, user, password) -> SurveillanceStation:
    ss = SurveillanceStation(ip_address=ip, port=port, username=user, password=password,
                             secure=True, cert_verify=False, dsm_version=7, debug=True,
                             otp_code=None)

    return ss


def syno_cameras(ss: SurveillanceStation) -> dict[str, object]:
    cameras_response = ss.camera_list()
    cameras = cameras_response['data']['cameras']
    logging.info('camera_list %s', json.dumps(cameras))
    for camera in cameras:
        logging.info('camera %s - %s - %s', camera['newName'], camera['model'], camera['vendor'])
    return cameras


def syno_camera_events(ss: SurveillanceStation, from_time: datetime) -> dict[str, object]:
    camera_events_response = ss.query_event_list_by_filter(limit=100, fromTime=int(from_time.timestamp()))
    camera_events = camera_events_response['data']['recordings']
    logging.info('camera_events %s', json.dumps(camera_events))
    for camera_event in camera_events:
        logging.info('camera %s - %s - %s', camera_event['id'], camera_event['cameraId'], camera_event['cameraName'],
                     camera_event['filePath'])
    return camera_events


def syno_recording_export(ss: SurveillanceStation, download_dir: str, event_id: int) -> str:
    recording_export_response = ss.download_recordings(id=event_id)
    recording_export_file = __save_recording_to_file__(download_response=recording_export_response,
                                                       download_dir=download_dir,
                                                       event_id=event_id)

    logging.info('recording_export %s', recording_export_file)
    return recording_export_file


def __save_recording_to_file__(download_response: dict[str, object], download_dir: str, event_id: str) -> str:
    outfile_gif = '{}/{}.mp4'.format(download_dir, event_id)

    with open(outfile_gif, "wb") as f:
        logging.info('Downloading video for event id %i to %s .....', event_id, outfile_gif)
        logging.info('download_response status_code %s', download_response.status_code)

        if download_response.ok:
            total_length = download_response.headers.get('content-length')

            if total_length is None:  # no content length header
                f.write(download_response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in download_response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                    sys.stdout.flush()
            logging.info('Downloading video for event id %i to %s .....DONE', event_id, outfile_gif)
            return outfile_gif

    return ''
