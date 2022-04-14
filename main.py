import configparser
import os
import sys
from collections import OrderedDict
from pathlib import Path

import typer
from pykeepass import PyKeePass
from rich.console import Console

app = typer.Typer()
console = Console()
error_console = Console(stderr=True, style='bold red')
config = configparser.ConfigParser()

config_path = os.environ.get(
    'AELLO_CONFIG_PATH', Path.home() / Path('.config/aello/config.ini')
)
config.read(config_path)

database_path = Path(config['keepass']['path'])
if not database_path.exists() and not database_path.is_file():
    error_console.print('Looks like the database does not exists.')
    error_console.print('Maybe you misspelled it, please check your config.')
    error_console.print(f'This is the path used: [underline]{database_path}')
    raise typer.Exit(code=1)

database = PyKeePass(
    str(database_path), password=config['keepass']['password']
)


@app.command()
def search(name: str):
    entries = database.find_entries(title=f'.*{name}.*', regex=True)
    if not entries:
        error_console.print(f'No entries found with "{name}" in the database')
        raise typer.Abort()

    for entry in entries:
        console.print(f'{entry.group} | {entry.title} | {entry.password}')


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        from app import KeePassApp
        from helpers import collect_entries, collect_groups

        tree = collect_groups(database.root_group)
        entries = collect_entries(database.entries)

        KeePassApp(title='Aello').run(
            keepass_tree=tree, keepass_entries=entries
        )


if __name__ == '__main__':
    app()
