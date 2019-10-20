from functools import reduce
from itertools import accumulate, takewhile

from reader import Reader
from utils import decode_sfn, decode_lfn, groupby


class FATException(Exception):
    pass


class FATIndexOutOfBounds(FATException):
    pass


class FATEntryError(FATException):
    pass


class FATEntryNonDirectory(FATEntryError):
    pass


class FATEntryNonFile(FATEntryError):
    pass


def not_implemented():
    return NotImplementedError("Not implemented")


class FATTable:
    def __init__(self, reader, base_ptr, size):
        self.reader = reader
        self.base_ptr = base_ptr
        self.size = size

    def _validate_idx(self, idx):
        raise not_implemented()

    def _get(self, idx):
        self._validate_idx(idx)
        raise not_implemented()

    def _is_eof(self, val):
        raise not_implemented()

    def __getitem__(self, item):
        self._validate_idx(item)
        return self._get(item)

    def iter(self, idx):
        self._validate_idx(idx)

        return takewhile(
            lambda c: not self._is_eof(c),
            accumulate(
                iter(lambda: idx, None),
                lambda a, _: self[a]
            )
        )


class FATEntryReader(Reader):
    def __init__(self, reader, table, cluster, cluster_size, data_ptr):
        self.reader = reader
        self.table = table
        self.cluster = cluster
        self.cluster_size = cluster_size
        self.data_ptr = data_ptr

    def read(self, size=0, rel_ptr=0, base_ptr=None):
        offset = rel_ptr + (base_ptr or 0)

        return reduce(
            lambda a, i: a + self.reader.read(
                self.cluster_size if size == 0 else min(size - len(a), self.cluster_size),
                (i[1] - 2) * self.cluster_size + offset % self.cluster_size,
                self.data_ptr
            ),
            takewhile(
                lambda c: size == 0 or c[0] * self.cluster_size < offset + size,
                filter(
                    lambda c: size == 0 or c[0] >= offset // self.cluster_size,
                    enumerate(self.table.iter(self.cluster))
                )
            ),
            bytearray()
        )

    def size(self):
        return reduce(
            lambda a, _: a + self.cluster_size,
            self.table.iter(self.cluster),
            0
        )


class FATEntry:
    def __init__(self, reader, table, cluster_size, params, data_ptr, lfn=None):
        self.reader = reader
        self.table = table
        self.cluster_size = cluster_size
        self.params = params
        self.lfn = lfn
        self.data_ptr = data_ptr
        self.entry_reader = self._create_entry_reader()

    def _create_entry_reader(self):
        raise not_implemented()

    def _create_dir_entry(self):
        raise not_implemented()

    @property
    def name(self):
        return decode_lfn(self.lfn) if self.lfn else ".".join(
            filter(
                lambda s: len(s),
                map(lambda s: decode_sfn(s).strip(), (self.params.Name, self.params.Ext))
            )
        )

    @property
    def is_readonly(self):
        return self.params.DOSPerms & 0x1

    @property
    def is_hidden(self):
        return self.params.DOSPerms & 0x2

    @property
    def is_system(self):
        return self.params.DOSPerms & 0x8

    @property
    def is_directory(self):
        return self.params.DOSPerms & 0x10

    @property
    def is_archive(self):
        return self.params.DOSPerms & 0x20

    @property
    def size(self):
        return self.params.FileSize

    def read(self, size=0, offset=0):
        if self.is_directory:
            raise FATEntryNonFile("Could not read directory as a file")

        return self.entry_reader.read(min(size, self.size) or self.size, offset)

    def __iter__(self):
        if not self.is_directory:
            raise FATEntryNonDirectory("Could not enumerate file entry")

        yield from self._create_dir_entry()


class FATDir:
    def __init__(self, table, reader, base_ptr, size, cluster_size, data_ptr):
        self.table = table
        self.reader = reader
        self.base_ptr = base_ptr
        self.size = size
        self.cluster_size = cluster_size
        self.data_ptr = data_ptr

    def _parse_entry(self, data):
        raise not_implemented()

    def _get_entry_class(self):
        raise not_implemented()

    def _get_lfn_struct(self):
        raise not_implemented()

    def _get_entry_struct(self):
        raise not_implemented()

    def _get_entry_size(self):
        raise not_implemented()

    def __iter__(self):
        return map(
            lambda g: self._get_entry_class()(
                self.reader,
                self.table,
                self.cluster_size,
                g[-1],
                self.data_ptr,
                reduce(
                    lambda a, i: b"".join((a or b"", i.Name5, i.Name6, i.Name2)),
                    sorted(
                        filter(
                            lambda i: i.SeqNumber != 0xE5 and i.SeqNumber <= 0x4F, g[:-1]
                        ),
                        key=lambda i: i.SeqNumber & 0x1F
                    ),
                    None
                )
            ),
            map(
                list,
                groupby(
                    lambda l, i: all(
                        map(lambda a: isinstance(*a),
                            ((l, self._get_lfn_struct()), (i, (self._get_entry_struct(), self._get_lfn_struct()))))
                    ),
                    takewhile(
                        lambda i: isinstance(i, self._get_lfn_struct()) or any(
                            map(lambda s: s[0] != 0, (i.Name, i.Ext))
                        ),
                        map(lambda i: self._parse_entry(
                            self.reader.read(self._get_entry_size(), i * self._get_entry_size(), self.base_ptr)),
                            range(int(self.size // self._get_entry_size())))
                    )
                )
            )
        )


class FATReader:
    def __init__(self, reader):
        self.reader = reader

    def read_bs(self):
        raise not_implemented()
