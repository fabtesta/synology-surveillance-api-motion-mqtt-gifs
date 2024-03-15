from dataclasses import dataclass
from typing import Optional


@dataclass
class CameraConfig:
    id: int
    mqtt_message_type: str
    mode: str
    scale: int
    topic_name: str
    skip_first_n_secs: Optional[int] = -1
    max_length_secs: Optional[int] = -1

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
