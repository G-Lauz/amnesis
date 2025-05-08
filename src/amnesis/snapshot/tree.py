from typing import List, Union

from .index import Index
from .objects import Object


def get_snapshot_tree(index: Index, ignore: Union[str, List[str]] = None) -> Object:
    if ignore is None:
        ignore = []

    if isinstance(ignore, str):
        ignore = [ignore]

    entries = index.read_index()
    entries = sorted(entries, key=lambda x: x.path)

    lines = []
    for entry in entries:
        if entry.path in ignore:
            continue

        lines.append(f"{entry.file_type} {entry.sha1} {entry.path}")

    data = "\n".join(lines).encode("utf-8")

    return Object(data, "tree")
