import dataclasses
import hashlib
import pathlib
from typing import List, Set, Union

from .objects import Object


@dataclasses.dataclass(frozen=True, order=True)
class IndexEntry:
    file_type: str
    sha1: str
    path: str


class Index:
    def __init__(self, root: str):
        """
        Initialize the index with the root directory of the repository.
        """
        self.root = pathlib.Path(root).resolve()
        self.index_file = self.root / ".amnesis" / "index"

    def read_index(self) -> Set[IndexEntry]:
        """
        Read the index file and return a set of tracked files.
        """
        if not self.index_file.exists():
            return set()

        with open(self.index_file, "r", encoding="utf-8") as file:
            data = file.read()

        digest = hashlib.sha1(data[:-40].encode("utf-8")).hexdigest()

        if digest != data[-40:]:
            raise ValueError("Index file is corrupted")

        lines = data.splitlines()

        entries = set()
        for line in lines[2:-1]:
            file_type, sha1, path = line.strip().split(" ", 2)
            entry = IndexEntry(file_type=file_type, sha1=sha1, path=path)
            entries.add(entry)

        return entries

    def write_index(self, entries: Set[IndexEntry]):
        """
        Write the index file with the tracked files.
        """
        # digest header
        version = "version: 0.1"
        length = len(entries)
        header = f"{version}\n{length}\n"
        content = (
            "\n".join(
                [f"{entry.file_type} {entry.sha1} {entry.path}" for entry in entries]
            )
            + "\n"
        )
        sha1 = hashlib.sha1((header + content).encode("utf-8")).hexdigest()

        with open(self.index_file, "w", encoding="utf-8") as file:
            file.write(header)
            file.write(content)
            file.write(sha1)

    def add(self, paths: Union[str, pathlib.Path, List[str], List[pathlib.Path]]):
        """
        Add a file or a list of files to the index.
        """
        if isinstance(paths, str) or isinstance(paths, pathlib.Path):
            paths = [paths]

        entries = self.read_index()

        for path in paths:
            path = pathlib.Path(path).resolve()

            if not path.exists():
                raise FileNotFoundError(f"File {path} does not exist.")

            with open(path, "rb") as f:
                data = f.read()

            file_type = "blob"
            sha1 = Object(data, file_type).hash()

            entry = IndexEntry(
                file_type=file_type,
                sha1=sha1,
                path=str(path.relative_to(self.root)),
            )

            # Check if the entry already exists
            for existing_entry in entries:
                if existing_entry.path == entry.path:
                    print(f"File {path} is already in the index.")
                    break
            else:
                # Add the new entry to the index
                entries.add(entry)
                print(f"Added {path} to the index.")

        self.write_index(entries)
