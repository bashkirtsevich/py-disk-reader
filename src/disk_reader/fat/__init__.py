from functools import reduce
from itertools import accumulate, takewhile, repeat
from struct import unpack

from disk_reader.reader import Reader
from disk_reader.utils import groupby, slice_len


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


# region: Utils

def not_implemented():
    return NotImplementedError("Not implemented")


def decode_lfn(data):
    return (b"".join(
        takewhile(
            lambda p: p != b"\x00\x00", (
                data[i: i + 2] for i in range(0, len(data), 2)
            )
        ))
    ).decode("utf-16-le", errors="replace")


def decode_sfn(data):
    return (b"".join(
        map(
            lambda i: i.to_bytes(1, "little"),
            takewhile(
                lambda p: p != b"\x00", data
            )
        ))
    ).decode("ascii", errors="replace")


# endregion


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
                repeat(idx),
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
    DOS_PERMS_R = 0x1
    DOS_PERMS_H = 0x2
    DOS_PERMS_S = 0x8
    DOS_PERMS_D = 0x10
    DOS_PERMS_A = 0x20

    def __init__(self, basic_reader, entry_reader, table, cluster_size, params, data_ptr, lfn=None):
        self.basic_reader = basic_reader
        self.reader = entry_reader
        self.table = table
        self.cluster_size = cluster_size
        self.params = params
        self.lfn = lfn
        self.data_ptr = data_ptr
        self.entry_reader = self._create_entry_reader()

    @staticmethod
    def _get_entry_reader_class():
        raise not_implemented()

    @staticmethod
    def _get_dir_entry_class():
        raise not_implemented()

    def _create_entry_reader(self):
        return self._get_entry_reader_class()(
            self.basic_reader,
            self.table,
            self.params.ClusterHi << 16 | self.params.ClusterLo,
            self.cluster_size,
            self.data_ptr
        )

    def _create_dir_entry(self):
        return self._get_dir_entry_class()(
            self.table,
            self.basic_reader,
            self.entry_reader,
            0,
            self.entry_reader.size(),
            self.cluster_size,
            self.data_ptr
        )

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
        return self.params.DOSPerms & self.DOS_PERMS_R

    @property
    def is_hidden(self):
        return self.params.DOSPerms & self.DOS_PERMS_H

    @property
    def is_system(self):
        return self.params.DOSPerms & self.DOS_PERMS_S

    @property
    def is_directory(self):
        return self.params.DOSPerms & self.DOS_PERMS_D

    @property
    def is_archive(self):
        return self.params.DOSPerms & self.DOS_PERMS_A

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
    def __init__(self, table, basic_reader, entry_reader, base_ptr, size, cluster_size, data_ptr):
        self.table = table
        self.basic_reader = basic_reader
        self.entry_reader = entry_reader
        self.base_ptr = base_ptr
        self.size = size  # FIXME: self.size = size or reader.size()
        self.cluster_size = cluster_size
        self.data_ptr = data_ptr

    @staticmethod
    def _get_entry_perms():
        raise not_implemented()

    @staticmethod
    def _get_lfn():
        raise not_implemented()

    @staticmethod
    def _get_entry():
        raise not_implemented()

    @staticmethod
    def _get_entry_class():
        raise not_implemented()

    @staticmethod
    def _get_lfn_struct():
        raise not_implemented()

    @staticmethod
    def _get_entry_struct():
        raise not_implemented()

    @staticmethod
    def _get_entry_size():
        raise not_implemented()

    def _parse_entry(self, data):
        offset, size, unpack_str = self._get_entry_perms()
        return self._get_lfn_struct()(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in self._get_lfn())
            # FIXME: Use named constant instead value
        ) if unpack(unpack_str, data[slice_len(offset, size)])[0] == 0xF else self._get_entry_struct()(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in self._get_entry())
        )

    def __iter__(self):
        return map(
            lambda g: self._get_entry_class()(
                self.basic_reader,
                self.entry_reader,
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
                        key=lambda i: i.SeqNumber & 0x1F  # FIXME: Replace values to named constants
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
                            self.entry_reader.read(self._get_entry_size(), i * self._get_entry_size(), self.base_ptr)),
                            range(int(self.size // self._get_entry_size())))
                    )
                )
            )
        )


class FATBootSector:
    def __init__(self, reader):
        self.data = self._get_struct_class()(
            *(reader.unpack(unpack_str, size, offset)[0] for offset, size, _, unpack_str in self._get_sign())
        )

    @staticmethod
    def _get_sign():
        raise not_implemented()

    @staticmethod
    def _get_struct_class():
        raise not_implemented()

    @property
    def sector_size(self):
        return self.data.BytesPerSector

    @property
    def fats_offset(self):
        return self.data.SectorsCount * self.data.BytesPerSector

    @property
    def fats_copies(self):
        return self.data.FATCopies

    @property
    def fat_size(self):
        return self.data.SectorsPerFAT * self.data.BytesPerSector

    @property
    def cluster_size(self):
        return self.data.BytesPerSector * self.data.SectorsPerCluster

    @property
    def data_offset(self):
        return self.fats_offset + self.fats_copies * self.fat_size


class FATReader:
    def __init__(self, reader):
        self.reader = reader
        self.boot_sector = self.read_boot_sector()
        self.fats = self.read_fats()
        self.root_dir = self.read_root()

    def read_boot_sector(self):
        return self._get_boot_sector_class()(self.reader)

    def read_fats(self):
        return [
            self._get_fat_table_class()(
                self.reader,
                self.boot_sector.fats_offset + i * self.boot_sector.fat_size,
                self.boot_sector.fat_size
            ) for i in range(self.boot_sector.fats_copies)
        ]

    def read_root(self):
        raise not_implemented()

    @property
    def primary_fat(self):
        return self.fats[0]

    @staticmethod
    def _get_boot_sector_class():
        raise not_implemented()

    @staticmethod
    def _get_fat_table_class():
        raise not_implemented()

