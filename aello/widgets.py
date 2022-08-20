from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import rich.repr
from pykeepass.entry import Entry
from pykeepass.group import Group
from rich.console import RenderableType
from rich.text import Text
from textual.message import Message
from textual.reactive import Reactive
from textual.widgets import NodeID, TreeClick, TreeControl, TreeNode


@dataclass
class TreeEntry:
    id: str
    name: str
    path: str
    is_group: bool
    keepass_instance: Literal[Group, Entry]


'''

@rich.repr.auto
class TreeEntryClick(Message, bubble=True):
    def __init__(self, sender, path: str) -> None:
        self.node = node
        super().__init__(sender)

'''


class KeePassTree(TreeControl[TreeEntry]):
    has_focus: Reactive[bool] = Reactive(False)

    def __init__(self, *args, **kwargs) -> None:
        """
        Creates a directory tree struction from KeePass groups and entries.
        This class is a copy of textual.widgets.DirectoryTree with ammendments
        """
        instance = TreeEntry(**kwargs)
        super().__init__(
            label=instance.name, name=instance.name, data=instance
        )
        self.root.tree.guide_style = 'black'

    def on_focus(self) -> None:
        """Sets has_focus to true when the item is clicked."""
        self.has_focus = True

    def on_blur(self) -> None:
        """Sets has_focus to false when an item no longer has focus."""
        self.has_focus = False

    async def watch_hover_node(self, hover_node: NodeID) -> None:
        """
        Configures styles for a node when hovered over by the mouse pointer.
        """
        for node in self.nodes.values():
            node.tree.guide_style = (
                'bold not dim red' if node.id == hover_node else 'black'
            )

        self.refresh(layout=True)

    def render_node(self, node: TreeNode[TreeEntry]) -> RenderableType:
        """
        Renders a node in the tree.
        """
        return self.render_tree_label(
            node,
            node.data.is_group,
            node.expanded,
            node.is_cursor,
            node.id == self.hover_node,
            self.has_focus,
        )

    @lru_cache(maxsize=1024 * 32)
    def render_tree_label(
        self,
        node: TreeNode[TreeEntry],
        is_group: bool,
        expanded: bool,
        is_cursor: bool,
        is_hover: bool,
        has_focus: bool,
    ) -> RenderableType:
        meta = {
            '@click': f'click_label({node.id})',
            'tree_node': node.id,
            'cursor': node.is_cursor,
        }

        label = Text(node.label) if isinstance(node.label, str) else node.label

        if is_hover:
            label.stylize('underline')

        if is_group:
            label.stylize('bold magenta')
            icon = '📂' if expanded else '📁'
        else:
            label.stylize('bright_green')
            icon = '📄'
            label.highlight_regex(r'\..*$', 'green')

        if is_cursor and has_focus:
            label.stylize('reverse')

        icon_label = (
            Text(f'{icon} ', no_wrap=True, overflow='ellipsis') + label
        )
        icon_label.apply_meta(meta)
        return icon_label

    async def on_mount(self) -> None:
        """
        Actions that are executed when the widget is mounted.
        """
        await self.load_tree(self.root)

    async def load_tree(self, node: TreeNode[TreeEntry]):
        """
        Load entry for a tree node.
        """
        entries = (
            node.data.keepass_instance.subgroups
            + node.data.keepass_instance.entries
        )

        for item in entries:
            name = item.name if isinstance(item, Group) else item.title
            instance = TreeEntry(
                id=str(item.uuid),
                name=name or '--',
                path='/'.join('' if p == None else p for p in item.path),
                is_group=isinstance(item, Group),
                keepass_instance=item,
            )
            await node.add(name or '--', instance)

        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[TreeEntry]) -> None:
        """
        Handle messages that are sent when a tree item is clicked.
        """
        entry = message.node.data

        if not entry.is_group:
            await self.emit(TreeClick(self, message.node))
        else:
            if not message.node.loaded:
                await self.load_tree(message.node)
                await message.node.expand()
            else:
                await message.node.toggle()
