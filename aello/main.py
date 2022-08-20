import os
from collections import OrderedDict
from pathlib import Path

import typer
from pykeepass import PyKeePass
from rich.console import Console

from .config import Config

app = typer.Typer()
console = Console()
error_console = Console(stderr=True, style='bold red')

config_path = os.environ.get(
    'AELLO_CONFIG_PATH', Path.home() / Path('.config/aello/config.ini')
)
config = Config.setup(config_path)

database = PyKeePass(config.keepass.path, password=config.keepass.password)

if config.app.mode == 'compact':
    from .app import KeePassCompact

    App = KeePassCompact

if config.app.mode == 'full':
    from .app import KeePassFull

    App = KeePassFull


@app.command()
def search(name: str):
    from .helpers import collect_entries, collect_groups

    entries = database.find_entries(title=f'.*{name}.*', regex=True)
    if not entries:
        error_console.print(f'No entries found with "{name}" in the database')
        raise typer.Abort()

    tree = collect_groups(database.root_group)
    entries = collect_entries(database.entries)
    App(title='aello').run(keepass_tree=tree, keepass_entries=entries)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        from .helpers import collect_entries, collect_groups

        # tree = collect_groups(database.root_group)
        entries = collect_entries(database.entries)
        App(title='aello').run(
            sidebar_position=config.app.sidebar_position,
            keepass_root=database.root_group,
            keepass_entries=entries,
        )
