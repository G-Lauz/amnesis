import abc
import hashlib
import pathlib
import zlib


class Object(abc.ABC):
    def __init__(self, data: bytes, object_type: str, metadata: dict = None):
        self._data = data
        self.object_type = object_type
        self.metadata = metadata

    def __hash__(self):
        digest = self.hash()
        return int(digest, 16)

    def hash(self):
        """
        Returns the hash of the experiment as a hexadecimal string.
        This is a 40-character string representing the SHA-256 hash of the experiment.
        """
        return hashlib.sha256(self._data).hexdigest()

    @property
    def data(self) -> bytes:

        metadata = b""
        if self.metadata:
            metadata = "\n".join(f"{k}: {v}" for k, v in self.metadata.items()).encode(
                "utf-8"
            )

        header = f"{self.object_type} {len(metadata)} {len(self._data)}".encode("utf-8")

        return header + b"\x00" + metadata + b"\x00" + self._data

    @staticmethod
    def create_object(data: bytes) -> "Object":
        null_byte_index = data.index(b"\x00")
        header = data[:null_byte_index]

        object_type, len_meta, len_data = header.decode("utf-8").split(" ")
        len_data = int(len_data)
        len_meta = int(len_meta)

        metadata_start = null_byte_index + 1
        metadata_end = metadata_start + len_meta
        metadata_bytes = data[metadata_start:metadata_end]

        obj_data_start = metadata_end + 1
        obj_data = data[obj_data_start:]

        metadata_dict = {}
        if len_meta > 0:
            if len(metadata_bytes) != len_meta:
                raise ValueError(
                    f"Metadata size mismatch: expected {len_meta}, got {len(metadata_bytes)}"
                )

            metadata_str = metadata_bytes.decode("utf-8").splitlines()
            for line in metadata_str:
                key, value = line.split(": ", 1)
                metadata_dict[key] = value

        if len(obj_data) != len_data:
            raise ValueError(
                f"Data size mismatch: expected {len_data}, got {len(obj_data)}"
            )

        return Object(obj_data, object_type, metadata=metadata_dict)


class ObjectStore(abc.ABC):
    def __init__(self, path: str):
        self.path = pathlib.Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def write(self, obj: Object) -> None:
        """
        Write the object to the object store under `object_store_path/object_hash`.
        """
        object_hash = obj.hash()
        object_path = pathlib.Path(self.path / object_hash)

        object_path.parent.mkdir(parents=True, exist_ok=True)

        compressed_data = zlib.compress(obj.data)
        with open(object_path, "wb") as f:
            f.write(compressed_data)

    def read(self, object_hash: str) -> Object:
        """
        Read the object from the object store under `object_store_path/object_hash`.
        """
        object_path = self.path / object_hash
        if not object_path.exists():
            raise FileNotFoundError(f"Object {object_hash} not found in {self.path}")

        with open(object_path, "rb") as f:
            compressed_data = f.read()

        data = zlib.decompress(compressed_data)

        return Object.create_object(data)
