import pathlib
from difflib import SequenceMatcher
from typing import List, Union

from .objects import ObjectStore
from .patch import Patch, PatchChunk


class DiffEngine:

    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.obj_store = ObjectStore(self.root / ".amnesis" / "objects")

    @staticmethod
    def compute_patch(old_lines: List[str], new_lines: List[str]) -> List[PatchChunk]:
        """
        Compute a compact diff between two versions using SequenceMatcher.
        Only changed regions are stored.
        """
        matcher = SequenceMatcher(None, old_lines, new_lines)

        chunks = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            chunks.append(PatchChunk(tag, i1, i2, j1, j2, new_lines[j1:j2]))

        return chunks

    @staticmethod
    def apply_patch(base_lines: List[str], patch: List[PatchChunk]) -> List[str]:
        result: List[str] = []
        index = 0

        for chunk in patch:
            # unchanged before chunk
            result.extend(base_lines[index : chunk.old_start])

            if chunk.tag in ("insert", "replace"):
                result.extend(chunk.new_lines)
            # 'delete' means skip

            index = chunk.old_end

        # remaining tail
        result.extend(base_lines[index:])
        return result

    def restore_patch(self, patch: Union[str, Patch]) -> List[str]:
        """
        Recursively restore content from a Patch object.

        :param patch: Patch object containing parent, and content
        :return: restored list of lines
        """
        obj = None
        if isinstance(patch, str):
            obj = self.obj_store.read(patch)

        if isinstance(patch, Patch):
            obj = patch.get_object()

        if obj.object_type == "blob":
            return obj._data.decode("utf-8").splitlines(keepends=True)

        patch = Patch.from_object(obj)

        # Restore parent first
        restored_parent = self.restore_patch(patch.parent)

        # Apply current patch to the restored parent
        if isinstance(patch.content, list) and all(
            isinstance(item, PatchChunk) for item in patch.content
        ):
            return self.apply_patch(restored_parent, patch.content)

        raise TypeError("Invalid patch content type")

    @staticmethod
    def format_unified(
        patch: List[PatchChunk],
        old_lines: List[str],
        fromfile: str = "old",
        tofile: str = "new",
    ) -> str:
        """
        Turn a list of PatchChunks into a unified diff-style string.

        :param patch: list of PatchChunk
        :param old_lines: original lines (with \n)
        :param fromfile: header filename for old side
        :param tofile: header filename for new side
        :return: unified diff string
        """
        lines: List[str] = []
        lines.append(f"--- {fromfile}")
        lines.append(f"+++ {tofile}")

        for chunk in patch:
            old_count = chunk.old_end - chunk.old_start
            new_count = chunk.new_end - chunk.new_start
            hunk = f"@@ -{chunk.old_start+1},{old_count} +{chunk.new_start+1},{new_count} @@"
            lines.append(hunk)

            # deletions
            if chunk.tag in ("delete", "replace"):
                for ln in old_lines[chunk.old_start : chunk.old_end]:
                    lines.append(f"-{ln.rstrip()}")

            # insertions
            if chunk.tag in ("insert", "replace"):
                for ln in chunk.new_lines:
                    lines.append(f"+{ln.rstrip()}")

        return "\n".join(lines) + "\n"
