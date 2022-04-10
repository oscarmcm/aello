import os
import sys
import configparser
from pathlib import Path
import typer
from pykeepass import PyKeePass
from rich.console import Console

app = typer.Typer()
console = Console()
error_console = Console(stderr=True, style="bold red")

config = configparser.ConfigParser()
config_path = os.environ.get(
    'AELLO_CONFIG_PATH',
    Path.home() / Path('.config/aello/config.ini')
)
config.read(config_path)

database_path = Path(config['keepass']['path'])
if not database_path.exists() and not database_path.is_file():
    error_console.print('Looks like the database dont exists.')
    error_console.print('Maybe you misspelled it, please check your config.')
    error_console.print(f'This is the path used: [underline]{database_path}')
    sys.exit(1)

database = PyKeePass(
    str(database_path), password=config['keepass']['password']
)

@app.command()
def search(name: str):
    entries = database.find_entries(title=f'{name}*', regex=True)
    if not entries:
        error_console.print(f'No entries found with "{name}" in the database')
    console.print(entries)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(config['keepass']['password'])


if __name__ == "__main__":
    app()
