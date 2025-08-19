import pathlib
from typing import List, Set, Tuple, Union

from amnesis.experiment import Experiment
from amnesis.manifest import Manifest

from .diff import DiffEngine
from .index import Index
from .objects import Object, ObjectStore
from .patch import Patch
from .tree import Tree, TreeEntry


class Snapshot:
    def __init__(self, root: str, model_dir: str, ignore: Union[str, List[str]] = None):
        self.root = pathlib.Path(root).resolve()

        self.obj_store = ObjectStore(self.root / ".amnesis" / "objects")

        self.index = Index(self.root)
        self.model_dir = model_dir

        self.ignore = ignore if ignore is not None else []

    def get_last_tree_entries(self, manifest: Manifest) -> Set[TreeEntry]:
        parent_hash = None
        manifest_entries = manifest.read_manifest()

        if not manifest_entries:
            return set()

        last_experiment = manifest_entries[-1]
        parent_hash = last_experiment.sha1

        if not parent_hash:
            return set()

        last_experiment = Experiment.load(
            self.model_dir / parent_hash / "metadata.json"
        )
        last_tree = last_experiment.tree

        last_tree_obj = self.obj_store.read(last_tree)
        last_tree = Tree(self.index, ignore=None)
        entries = last_tree.read_tree(last_tree_obj)
        return set(entries)

    def get_changes(
        self, old_entries: Set[TreeEntry], new_entries: Set[TreeEntry]
    ) -> Set[Tuple[TreeEntry]]:
        common_entries = set()
        changed = set()

        for entry in new_entries:
            for old_entry in old_entries:
                if entry.path == old_entry.path:
                    if entry.sha1 != old_entry.sha1:
                        changed.add((old_entry, entry))

                    common_entries.add(entry)
                    break

        removed = old_entries - common_entries
        added = new_entries - common_entries

        return added, changed, removed

    def get_common_files_entries(
        self, old_entries: Set[TreeEntry], new_entries: Set[TreeEntry]
    ) -> Set[TreeEntry]:
        common_entries = set()

        for entry in new_entries:
            for old_entry in old_entries:
                if entry.path == old_entry.path:
                    common_entries.add(entry)
                    break

        return common_entries

    def create_snapshot(self) -> Object:
        # Fetch parent tree
        manifest = Manifest(self.model_dir)

        old_entries = self.get_last_tree_entries(manifest)
        old_entries_dict = {entry.path: entry for entry in old_entries}

        tracked_entries = self.index.read_index()

        common_entries = self.get_common_files_entries(old_entries, tracked_entries)
        added = old_entries - common_entries
        removed = tracked_entries - common_entries

        diff_engine = DiffEngine(self.root)

        for entry in common_entries:
            if entry.path in self.ignore:
                continue

            old_obj_entry = old_entries_dict.get(entry.path, None)
            old_obj = self.obj_store.read(old_obj_entry.sha1)

            old_file: List[str] = None
            if old_obj.object_type == "patch":
                patch = Patch.from_object(old_obj)
                old_file = diff_engine.restore_patch(patch)
            else:
                old_file = old_obj._data.decode("utf-8").splitlines(keepends=True)

            # read bytes
            with open(entry.path, "rb") as f:
                new_file = f.read().decode("utf-8").splitlines(keepends=True)

            chunks = diff_engine.compute_patch(old_file, new_file)
            patch = Patch(parent=old_obj_entry.sha1, content=chunks)
            patch_obj = patch.get_object()

            self.obj_store.write(patch_obj)
            self.index.update(patch_obj, entry.path)

        # Create a new tree object
        tree = Tree(self.index, ignore=self.ignore)
        tree_obj = tree.get_object()
        self.obj_store.write(tree_obj)

        return tree_obj
