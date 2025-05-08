import abc
import hashlib
import pathlib
import zlib


class Object(abc.ABC):
    def __init__(self, data: bytes, object_type: str):
        self._data = data
        self.object_type = object_type

        self.header = f"{object_type} {len(data)}".encode("utf-8")

    def __hash__(self):
        digest = self.hash()
        return int(digest, 16)

    def hash(self):
        """
        Returns the hash of the experiment as a hexadecimal string.
        This is a 40-character string representing the SHA-1 hash of the experiment.
        """
        return hashlib.sha1(self._data).hexdigest()

    @property
    def data(self) -> bytes:
        return self.header + b"\x00" + self._data

    @staticmethod
    def create_object(data: bytes) -> "Object":
        null_byte_index = data.index(b"\x00")
        header = data[:null_byte_index]

        object_type, size = header.decode("utf-8").split(" ")
        size = int(size)

        data = data[null_byte_index + 1 :]
        if len(data) != size:
            raise ValueError(f"Data size mismatch: expected {size}, got {len(data)}")

        return Object(data, object_type)


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
