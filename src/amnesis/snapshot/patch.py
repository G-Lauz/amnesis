import dataclasses
from typing import List, Union

from .objects import Object


@dataclasses.dataclass
class PatchChunk:
    tag: str
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    new_lines: List[str]


class Patch:

    def __init__(self, parent: str, content: Union[List[str], List[PatchChunk]] = None):
        self.parent = parent
        self.content = content

    def get_object(self) -> Object:
        """
        Get the Object representation of the Patch.
        The Object will have the type 'patch' and will contain the parent, diff and sha1.
        """
        metadata = {"parent": self.parent}

        diff = []
        for chunk in self.content:
            diff.append(
                f"{chunk.tag} {chunk.old_start} {chunk.old_end} {chunk.new_start} {chunk.new_end}\n{''.join(chunk.new_lines)}"
            )

        data = "\n".join(diff).encode("utf-8")

        return Object(data, "patch", metadata=metadata)

    @classmethod
    def from_object(cls, obj: Object) -> "Patch":
        """
        Create a Patch instance from an Object.
        The Object must be of type 'patch'.
        """
        if obj.object_type != "patch":
            raise ValueError("Object must be of type 'patch'")

        parent = obj.metadata.get("parent", None)

        if not parent:
            raise ValueError("Patch object must have a parent specified in metadata")

        diff = obj._data.decode("utf-8").split(sep="\n\n")

        content = []
        for line in diff:
            opcodes, *new_lines = line.split(sep="\n", maxsplit=1)
            tag, old_start, old_end, new_start, new_end = opcodes.split()

            if new_lines:
                new_lines = "".join(new_lines)
                new_lines = new_lines.splitlines(keepends=True)

            content.append(
                PatchChunk(
                    tag=tag,
                    old_start=int(old_start),
                    old_end=int(old_end),
                    new_start=int(new_start),
                    new_end=int(new_end),
                    new_lines=new_lines,
                )
            )

        return cls(parent=parent, content=content)
