import os
import sys
from rich.console import RenderableType

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App
from textual.widgets import Header, Footer, Placeholder, TreeNode, TreeControl, TreeClick, ScrollView
from rich.tree import Tree
from rich.panel import Panel


class KeePassApp(App):
    keepass_tree = None

    def __init__(self, *args, **kwargs):
        self.keepass_tree = kwargs.get('keepass_tree')
        super().__init__()
        
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
        
        def add_nodes(node, node_tree):
            if node_tree['items']:
                for tree_item in node_tree['items']:
                    _, item_name = tree_item
                    node.add(f'[bold yellow]{item_name}')
            if node_tree['groups']:
                for group in node_tree['groups']:
                    for node_name, tree in group.items():
                        new_node = Tree(node_name)
                        node.add(new_node)
                        add_nodes(new_node, tree)

        root = Tree('Root', hide_root=True)
        for node_name, tree in self.keepass_tree.items(): 
            node = root.add(f':file_folder: {node_name}')
            add_nodes(node, tree)
                    


        # Dock our widgets
        # await self.view.dock(Header(style='', clock=False), edge='top')
        await self.view.dock(Footer(), edge='bottom')

        # Note the directory is also in a scroll view
        await self.view.dock(
            ScrollView(root), edge='left', size=48, name='sidebar'
        )
        await self.view.dock(self.body, edge='top')
        foo = Panel('demo', title='Notes')
        await self.body.update(foo)
    
    async def handle_file_click(self, message: FileClick) -> None:
        """
        A message sent by the directory tree when a file is clicked.
        """

        syntax: RenderableType
        try:
            # Construct a Syntax object for the path in the message
            syntax = Syntax.from_path(
                message.path,
                line_numbers=True,
                word_wrap=True,
                indent_guides=True,
                theme="monokai",
            )
        except Exception:
            # Possibly a binary file
            # For demonstration purposes we will show the traceback
            syntax = Traceback(theme="monokai", width=None, show_locals=True)
        self.app.sub_title = os.path.basename(message.path)
        await self.body.update(syntax)
