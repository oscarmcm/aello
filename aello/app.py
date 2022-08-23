from collections import OrderedDict
from enum import Enum

import pyperclip
from pykeepass.group import Group as KeePassGroup
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.widgets import ScrollView, TreeClick

from .widgets import KeePassFooter, KeePassHeader, KeePassTree, Notification


class NotificationType(Enum):
    Error = {'border': 'red', 'background': 'default on red'}
    Success = {'border': 'green', 'background': 'black on green'}
    Warning = {'border': 'yellow', 'background': 'black on yellow'}


class Main(App):
    sidebar_position: str
    keepass_root_group: KeePassGroup
    keepass_entries: OrderedDict
    active_item: dict

    def __init__(self, *args, **kwargs):
        self.sidebar_position = kwargs.get('sidebar_position')
        self.keepass_root = kwargs.get('keepass_root')
        self.keepass_entries = kwargs.get('keepass_entries')
        super().__init__()

    async def fire_notification(self, message: str, mode: NotificationType):
        await self.view.dock(
            Notification(message, mode), z=1, edge='top', size=3
        )

    def render_body(self, key: str) -> RenderableType:
        self.active_item = self.keepass_entries.get(key)

        info_table = Table(
            box=None, padding=2, expand=True, show_header=False, leading=1
        )

        for key_name, key_value in self.active_item.items():
            if key_name == 'notes' or key_name.startswith('__'):
                continue
            info_table.add_row(key_name.title(), key_value)

        self.app.sub_title = self.active_item['__path']
        body = Group(Panel(info_table, title='Entry', title_align='left'))
        if self.active_item['notes']:
            body.renderables.append(
                Panel(
                    Text(self.active_item['notes']),
                    title='Notes',
                    title_align='left',
                ),
            )
        return body

    async def action_copy(self, key: str) -> None:
        try:
            pyperclip.copy(self.active_item[key])
            await self.fire_notification(
                f'Successfully copied {key}!', NotificationType.Success
            )
        except:
            await self.fire_notification(
                f'Unable to copy {key} from entry!', NotificationType.Error
            )

    async def on_load(self) -> None:
        """
        Sent before going in to application mode.
        """
        # await self.bind('b', 'view.toggle("sidebar")', 'Toggle sidebar')
        await self.bind('q', 'quit', 'Quit')
        await self.bind('esc', 'quit', 'Quit')
        await self.bind('p', 'copy("password")', 'Copy Password')
        await self.bind('u', 'copy("username")', 'Copy Username')
        await self.bind('l', 'copy("url")', 'Copy URL')

    async def handle_tree_click(self, message: TreeClick) -> None:
        """
        A message sent by the directory tree when a file is clicked.
        """
        entry = message.node.data
        if not entry.is_group:
            body_content = self.render_body(entry.id)
            await self.body.update(body_content)

        # if not message.node.empty:
        #    await message.node.toggle()


class KeePassFull(Main):
    async def on_mount(self) -> None:
        """
        Call after terminal goes in to application mode
        """
        self.app.title = 'aello'

        self.body = ScrollView()

        main_tree = KeePassTree(
            id=str(self.keepass_root.uuid),
            name=self.keepass_root.name,
            path='/',
            is_group=True,
            keepass_instance=self.keepass_root,
        )

        main_tree.loaded = True
        self.refresh(layout=True)

        await self.view.dock(KeePassHeader(), edge='top')
        await self.view.dock(KeePassFooter(), edge='bottom')

        await self.view.dock(
            ScrollView(main_tree),
            edge=self.sidebar_position,
            size=48,
            name='sidebar',
        )
        await self.view.dock(self.body, edge='top')


class KeePassCompact(Main):
    async def on_mount(self) -> None:
        self.body = ScrollView()
        await self.view.dock(self.body, edge='top')
