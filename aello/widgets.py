from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pykeepass.entry import Entry
from pykeepass.group import Group
from rich.box import Box
from rich.console import RenderableType
from rich.panel import Panel
from rich.repr import Result, rich_repr
from rich.text import Text
from textual.events import Blur, Enter, Focus, Leave, MouseMove
from textual.reactive import Reactive, watch
from textual.widget import Widget
from textual.widgets import NodeID, TreeClick, TreeControl, TreeNode

ONLY_TOP: Box = Box(
    """\
 ── 
    
 ── 
    
 ── 
 ── 
    
    
"""
)

ONLY_BOTTOM: Box = Box(
    """\
    
    
 ── 
    
 ── 
 ── 
    
 ── 
"""
)


@dataclass
class TreeEntry:
    id: str
    name: str
    path: str
    is_group: bool
    keepass_instance: Literal[Group, Entry]


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


class KeePassHeader(Widget):
    highlight_key: Reactive[str | None] = Reactive(None)

    def __init__(self) -> None:
        self.keys: list[tuple[str, str]] = []
        super().__init__()
        self.layout_size = 3
        self._key_text: Text | None = None

    async def watch_highlight_key(self, value) -> None:
        """If highlight key changes we need to regenerate the text."""
        self._key_text = None

    async def on_mouse_move(self, event: MouseMove) -> None:
        """Store any key we are moving over."""
        self.highlight_key = event.style.meta.get('key')

    async def on_leave(self, event: events.Leave) -> None:
        """Clear any highlight when the mouse leave the widget"""
        self.highlight_key = None

    def __rich_repr__(self) -> Result:
        yield 'keys', self.keys

    def make_key_text(self) -> Text:
        """
        Create text containing all the keys.
        """

        text = Text(
            style='white on default',
            no_wrap=True,
            overflow='ellipsis',
            justify='left',
            end='',
        )
        for binding in self.app.bindings.shown_keys:
            key_display = (
                binding.key
                if binding.key_display is None
                else binding.key_display.upper()
            )
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (
                    f' {key_display} ',
                    'reverse' if hovered else 'default on default',
                ),
                f' {binding.description} ',
                meta={
                    '@click': f'app.press("{binding.key}")',
                    'key': binding.key,
                },
            )
            text.append_text(key_text)
        return Panel(text, box=ONLY_BOTTOM)

    def render(self) -> RenderableType:
        if self._key_text is None:
            self._key_text = self.make_key_text()
        return self._key_text


class KeePassFooter(Widget):
    title: Reactive[str] = Reactive('')
    sub_title: Reactive[str] = Reactive('')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.layout_size = 3

    @property
    def full_title(self) -> str:
        return (
            f'{self.title} - {self.sub_title}'
            if self.sub_title
            else self.title
        )

    def __rich_repr__(self) -> Result:
        yield self.title

    def render(self) -> RenderableType:
        return Panel(
            Text(self.full_title, style='default on default'), box=ONLY_TOP
        )

    async def on_mount(self) -> None:
        self.set_interval(1.0, callback=self.refresh)

        async def set_title(title: str) -> None:
            self.title = title

        async def set_sub_title(sub_title: str) -> None:
            self.sub_title = sub_title

        watch(self.app, 'title', set_title)
        watch(self.app, 'sub_title', set_sub_title)


class Notification(Widget):
    counter = 0
    can_focus = False

    def __init__(self, message: str, mode, *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.message = message
        self.mode = mode.value

    def __rich_repr__(self) -> Result:
        yield 'name', self.name
        yield 'message', self.message

    def render(self) -> RenderableType:
        return Panel(
            Text(self.message, style=self.mode.get('background')),
            border_style=self.mode.get('border'),
            style=self.mode.get('background'),
            height=3,
            width=len(self.message) + 5,
            highlight=True,
            expand=False,
        )

    async def destroy(self):
        self.counter += 1
        if self.counter == 5:
            self.visible = False
            self._child_tasks.clear()
            self.app.view.layout.docks.pop()
            self.refresh(layout=True)

    async def on_mount(self) -> None:
        self.set_interval(1.0, callback=self.destroy)
