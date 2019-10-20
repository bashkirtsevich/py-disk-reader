from struct import unpack


class Reader:
    def read(self, size, rel_ptr=0, base_ptr=None):
        raise NotImplementedError("Not implemented")

    def unpack(self, unpack_str, size, rel_ptr=0, base_ptr=None):
        return unpack(unpack_str, self.read(size, rel_ptr, base_ptr))


class FileReader(Reader):
    def __init__(self, fs, base_ptr=None):
        super().__init__()

        self.fs = fs
        self.fs.seek(base_ptr or self.fs.tell())

    def read(self, size, rel_ptr=0, base_ptr=None):
        ptr = self.fs.tell()
        try:
            self.fs.seek((base_ptr or ptr) + rel_ptr)
            return self.fs.read(size)
        finally:
            self.fs.seek(ptr)
