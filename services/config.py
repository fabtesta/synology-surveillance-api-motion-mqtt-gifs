import json


def parse_config(config_path) -> dict[str, str]:
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data
