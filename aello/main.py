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
database_path = Path(config.keepass.path)
if not database_path.exists() and not database_path.is_file():
    error_console.print('Looks like the database does not exists.')
    error_console.print('Maybe you misspelled it, please check your config.')
    error_console.print(f'This is the path used: [underline]{database_path}')
    raise typer.Exit(code=1)


database = PyKeePass(
    str(database_path), password=config.keepass.password
)

if config.app.mode not in ['compact', 'full']:
    error_console.print(
        f'"{config.app.mode}" is not a valid or recognized app mode.'
    )
    error_console.print(
        'Use [underline]"compact" or [underline]"full" mode.'
    )
    raise typer.Exit(code=1)


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

        tree = collect_groups(database.root_group)
        entries = collect_entries(database.entries)
        App(title='aello').run(keepass_tree=tree, keepass_entries=entries)

