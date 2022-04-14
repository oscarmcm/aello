from collections import OrderedDict

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.reactive import Reactive
from textual.widgets import Footer, Placeholder, ScrollView, TreeClick
from widgets import KeePassTree


class KeePassApp(App):
    keepass_tree = None
    keepass_entries = None

    def __init__(self, *args, **kwargs):
        self.keepass_tree = kwargs.get('keepass_tree')
        self.keepass_entries = kwargs.get('keepass_entries')
        super().__init__()

    def render_body(self, key: str) -> RenderableType:
        data = self.keepass_entries.get(key)
        info_table = Table(
            box=None, padding=2, expand=True, show_header=False, leading=1
        )

        for key_name, key_value in data.items():
            if key_name == 'notes':
                continue
            info_table.add_row(key_name.title(), key_value)

        self.app.sub_title = data['title']
        return Group(
            Panel(info_table, title='Entry'),
            Panel(Text(data['notes']), title='Notes'),
        )

    async def on_load(self) -> None:
        """
        Sent before going in to application mode.
        """
        await self.bind('b', 'view.toggle("sidebar")', 'Toggle sidebar')
        await self.bind('q', 'quit', 'Quit')
        await self.bind('esc', 'quit', 'Quit')

    async def on_mount(self) -> None:
        """
        Call after terminal goes in to application mode
        """

        self.body = ScrollView()

        main_tree = KeePassTree(name='Root', id='', path='')
        main_tree.set_tree(self.keepass_tree)

        main_tree.loaded = True
        self.refresh(layout=True)

        await self.view.dock(Footer(), edge='bottom')
        await self.view.dock(
            ScrollView(main_tree), edge='left', size=48, name='sidebar'
        )
        await self.view.dock(self.body, edge='top')

    async def handle_tree_click(self, message: TreeClick) -> None:
        """
        A message sent by the directory tree when a file is clicked.
        """
        entry = message.node.data
        body_content = self.render_body(f'{entry.id}|{entry.path}')
        await self.body.update(body_content)

        if not message.node.empty:
            await message.node.toggle()

