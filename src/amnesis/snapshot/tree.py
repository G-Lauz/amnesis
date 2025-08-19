import dataclasses
from typing import List, Union

from .index import Index
from .objects import Object


@dataclasses.dataclass(frozen=True, order=True)
class TreeEntry:
    file_type: str
    sha1: str
    path: str


class Tree:
    def __init__(self, index: Index, ignore: Union[str, List[str]] = None):
        self.index = index

        self.ignore = ignore
        if self.ignore is None:
            self.ignore = []
        elif isinstance(self.ignore, str):
            self.ignore = [self.ignore]

    def get_object(self) -> Object:
        entries = self.index.read_index()
        entries = sorted(entries, key=lambda x: x.path)

        lines = []
        for entry in entries:
            if entry.path in self.ignore:
                continue

            lines.append(f"{entry.file_type} {entry.sha1} {entry.path}")

        data = "\n".join(lines).encode("utf-8")

        return Object(data, "tree")

    def read_tree(self, obj: Object) -> List[TreeEntry]:
        """
        Read the tree object and return a list of tree entries.
        """
        null_byte_index = obj.data.index(b"\x00")
        data = obj.data[null_byte_index + 1 :].decode("utf-8")

        lines = data.splitlines()

        entries = []
        for line in lines:
            file_type, sha1, path = line.strip().split(" ", 2)
            entry = TreeEntry(file_type=file_type, sha1=sha1, path=path)
            entries.append(entry)

        return entries
