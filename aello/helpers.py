from collections import OrderedDict

from pykeepass.entry import Entry
from pykeepass.group import Group


def collect_groups(group: Group) -> OrderedDict:
    """
    Collect KeePass group names and names of their children (entries)
    as a tree-like structure for easier printing.
    """
    result = OrderedDict()
    name = group.name
    if name not in result:
        result[name] = {
            'groups': [],
            'entries': [
                (entry.uuid, entry.path, entry.title)
                for entry in group.entries
            ],
        }

        for child in group.subgroups:
            result[name]['groups'].append(collect_groups(child))
    return result


def collect_entries(entries: list[Entry]) -> OrderedDict:
    """
    Collect all the KeePass entries for a better searchable content
    """
    result = OrderedDict()
    for entry in entries:
        result[f'{entry.uuid}|{entry.path}'] = {
            'title': entry.title,
            'username': entry.username,
            'password': entry.password,
            'URL': entry.url,
            'expires': 'Yes' if entry.expires else 'No',
            #'expires_on': entry.expires_on,
            'notes': entry.notes or '',
        }
    return result

