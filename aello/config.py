from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


Parser = ConfigParser()


@dataclass
class KeePassConfig:
    path: str
    password: str
    key: str
    transformed_key: str


@dataclass
class AppConfig:
    mode: list
    show_sidebar: bool


DefaultConfig = {
    'keepass': {'path': '', 'password': '', 'key': '', 'transformed_key': ''},
    'app': {'mode': 'compact', 'show_sidebar': False}
}


class Config:
    keepass: KeePassConfig
    app: AppConfig

    def __init__(self, keepass_conf, app_conf):
        self.keepass_conf = keepass_conf
        self.app_conf = app_conf

    @staticmethod
    def valid(config_path):
        config = Path(config_path)
        return config.exists() and config.is_file()

    @classmethod
    def setup(cls, config_path):
        if not cls.valid(config_path):
            Parser.read_dict(DefaultConfig)
        keepass_conf = KeePassConfig(**Parser['keepass'])
        app_conf = AppConfig(**Parser['app'])
        return cls(config_path, keepass_conf, app_conf)

