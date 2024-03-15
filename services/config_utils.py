import json

from model.CameraConfig import CameraConfig


def parse_config(config_path) -> dict[str, str]:
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data


def get_camera_config(cameras_config, camera_id) -> CameraConfig:
    for camera_config in cameras_config:
        if camera_config["id"] == camera_id:
            return CameraConfig(**camera_config)
    return None
