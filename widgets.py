from __future__ import annotations

import rich.repr

from rich.console import RenderableType
from rich.text import Text

from functools import lru_cache

from dataclasses import dataclass
from collections import OrderedDict
from textual.reactive import Reactive
from textual.widgets import TreeControl, TreeClick, TreeNode, NodeID


@dataclass
class Entry:
    """
    Represents the data
    """

    name: str
    id: str
    is_group: bool
    path: str


class KeePassTree(TreeControl[Entry]):
    tree_data: OrderedDict | None = None
    has_focus: Reactive[bool] = Reactive(False)

    def __init__(self, name: str, id: str, path: str) -> None:
        """
        Creates a directory tree struction from KeePass groups and entries.
        This class is a copy of textual.widgets.DirectoryTree with ammendments 
        """
        data = Entry(name=name, id=id, is_group=True, path=path)
        super().__init__(label='Root', name=name, data=data)
        #self.root.tree.guide_style = 'black'

    def set_tree(self, keepass_tree: OrderedDict) -> None:
        self.tree_data = keepass_tree

    def on_focus(self) -> None:
        """Sets has_focus to true when the item is clicked."""
        self.has_focus = True

    def on_blur(self) -> None:
        """Sets has_focus to false when an item no longer has focus."""
        self.has_focus = False

    async def action_click_label(self, node_id: NodeID) -> None:
        """
        Overrides action_click_label from tree control and sets show cursor to True
        """
        node = self.nodes[node_id]
        self.cursor = node.id
        self.cursor_line = self.find_cursor() or 0
        self.show_cursor = True
        await self.post_message(TreeClick(self, node))

    async def watch_hover_node(self, hover_node: NodeID) -> None:
        """
        Configures styles for a node when hovered over by the mouse pointer.
        """
        for node in self.nodes.values():
            node.tree.guide_style = (
                'bold not dim red' if node.id == hover_node else 'black'
            )

        self.refresh(layout=True)

    def render_node(self, node: TreeNode[Entry]) -> RenderableType:
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
        node: TreeNode[Entry],
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
            label.highlight_regex(r'\..*$', "green")


        if is_cursor and has_focus:
            label.stylize('reverse')

        icon_label = Text(f'{icon} ', no_wrap=True, overflow='ellipsis') + label
        icon_label.apply_meta(meta)
        return icon_label

    async def on_mount(self) -> None:
        """
        Actions that are executed when the widget is mounted.
        """
        for node_name, node_tree in self.tree_data.items():
            await self.load_tree(self.root, node_name, node_tree)

    async def load_tree(self, node: TreeNode[Entry], name:str, node_tree):
        """
        Load entry for a tree node.
        """
        node_entries = node_tree.get('entries')
        node_groups = node_tree.get('groups')

        if node_entries:
            for node_entry in node_entries:
                item_id, item_path, item_name = node_entry
                entry = Entry(
                    name=item_name,
                    id=item_id,
                    is_group=False,
                    path=item_path,
                )
                await node.add(item_name, entry)
        
        if node_groups:
            for group in node_groups:
                for node_name, groups in group.items():
                    node_group = Entry(
                        name=node_name,
                        id='',
                        is_group=True,
                        path='',
                    )
                    await node.add(node_name, node_group)
                    await self.load_tree(node, node_name, groups)

        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[Entry]) -> None:
        """
        Handle messages that are sent when a tree item is clicked.
        """
        node_data = message.node.data

        if not node_data.is_group:
            await self.emit(TreeClick(self, message.node))
        else:
            if not message.node.loaded:
                await self.load_tree(message.node)
                await message.node.expand()
            else:
                await message.node.toggle()
