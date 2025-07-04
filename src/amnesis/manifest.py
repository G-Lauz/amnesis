import dataclasses
import pathlib


@dataclasses.dataclass()
class ManifestEntry:
    date: str
    name: str
    sha1: str


class Manifest:
    """
    The manifest is an ordered list of all the experiments in the repository.
    It is ordered in chronological order, with the oldest experiment at the top of the file.
    The manifest is stored in the `.amnesis` directory of the repository.
    """

    def __init__(self, root: str):
        """
        Initialize the manifest with the root directory of the repository.
        """
        self.root = pathlib.Path(root).resolve()
        self.manifest_file = self.root / "manifest"

        if not self.manifest_file.exists():
            self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
            self.manifest_file.touch()

    def read_manifest(self) -> list[ManifestEntry]:
        """
        Read the manifest file and return a list of experiments.
        """
        if not self.manifest_file.exists():
            return []

        with open(self.manifest_file, "r", encoding="utf-8") as file:
            data = file.read()

        lines = data.splitlines()

        entries = []
        for line in lines:
            date, name, sha1 = line.strip().split(" ", 3)
            entry = ManifestEntry(date=date, name=name, sha1=sha1)
            entries.append(entry)

        return entries

    def add(self, entry: ManifestEntry):
        """
        Add an experiment to the manifest.
        """
        with open(self.manifest_file, "a", encoding="utf-8") as file:
            file.write(f"{entry.date} {entry.name} {entry.sha1}\n")
