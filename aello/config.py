from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich.console import Console
from typer import Exit as TyperExit

Parser = ConfigParser()
Error = Console(stderr=True, style='bold red')


@dataclass
class KeePassConfig:
    path: str
    password: str
    key: str = ''
    transformed_key: str = ''


@dataclass
class AppConfig:
    mode: Literal['compact', 'full'] = 'full'
    show_sidebar: bool = True
    sidebar_position: Literal['left', 'right'] = 'left'


DefaultConfig = {
    'keepass': {'path': '', 'password': '', 'key': '', 'transformed_key': ''},
    'app': {'mode': 'full', 'show_sidebar': True, 'sidebar_position': 'left'},
}


class Config:
    def __init__(
        self, keepass_conf: KeePassConfig, app_config: AppConfig
    ) -> None:
        self.keepass = keepass_conf
        self.app = app_config

    @staticmethod
    def valid_path(config_path) -> bool:
        file = Path(config_path)
        return file.exists() and file.is_file()

    @classmethod
    def setup(cls, config_path):
        if not cls.valid_path(config_path):
            Parser.read_dict(DefaultConfig)
        else:
            Parser.read_file(open(config_path))

        if 'keepass' not in Parser.sections():
            Error.print('Looks like you havent created a configuration file.')
            raise TyperExit(code=1)

        keepass_conf = KeePassConfig(**Parser['keepass'])
        if not cls.valid_path(keepass_conf.path):
            Error.print('Looks like the database does not exists.')
            Error.print(
                'Maybe you have a typo in the path, please check your config.'
            )
            Error.print(
                f'This is the path used: [underline]{keepass_conf.path}'
            )
            raise TyperExit(code=1)

        if 'app' not in Parser.sections():
            app_conf = AppConfig(**DefaultConfig['app'])
        else:
            app_conf = AppConfig(**Parser['app'])

        if app_conf.mode not in ['compact', 'full']:
            Error.print(
                f'"{app_conf.mode}" is not a valid or recognized app mode.'
            )
            Error.print('Use [underline]"compact" or [underline]"full" mode.')
            raise TyperExit(code=1)

        return cls(keepass_conf, app_conf)
