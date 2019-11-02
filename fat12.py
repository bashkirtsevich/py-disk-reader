from struct import unpack

from fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir
from signatures import *
from utils import slice_len

FAT12_STRUCT = namedtuple("FAT12", (it[2] for it in FAT12_SIGN))
FAT_12_ENTRY_STRUCT = namedtuple("FAT12Directory", (it[2] for it in FAT12_ENTRY))
FAT_12_LFN_STRUCT = namedtuple("FAT12LFN", (it[2] for it in FAT12_LFN))


class FAT12Table(FATTable):
    FAT12_ENTRY_START = 0x002
    FAT12_ENTRY_END = 0xFEF

    def _get(self, idx):
        return (int.from_bytes(
            self.reader.read(2, int(idx * 1.5), self.base_ptr),
            "little"
        ) >> (0 if (idx % 2 == 0) else 4)) & 0xFFF

    def _validate_idx(self, idx):
        if idx * 1.5 > self.size:
            # TODO: Make OutOfBoundsException
            raise Exception("Out of bounds")

    def _is_eof(self, val):
        # FIXME: Use DeMorgan rule
        return not (self.FAT12_ENTRY_START <= val <= self.FAT12_ENTRY_END)


class Fat12EntryReader(FATEntryReader):
    pass


class FAT12Entry(FATEntry):
    def _create_entry_reader(self):
        return Fat12EntryReader(
            self.basic_reader,
            self.table,
            self.params.ClusterHi << 16 | self.params.ClusterLo,
            self.cluster_size,
            self.data_ptr
        )

    def _create_dir_entry(self):
        return FAT12Dir(
            self.table,
            self.basic_reader,
            self.entry_reader,
            0,
            self.entry_reader.size(),
            self.cluster_size,
            self.data_ptr
        )


class FAT12Dir(FATDir):
    def _parse_entry(self, data):
        offset, size, unpack_str = FAT12_ENTRY_PERMS

        return FAT_12_LFN_STRUCT(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in FAT12_LFN)
        ) if unpack(unpack_str, data[slice_len(offset, size)])[0] == 0xF else FAT_12_ENTRY_STRUCT(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in FAT12_ENTRY)
        )

    def _get_entry_class(self):
        return FAT12Entry

    def _get_lfn_struct(self):
        return FAT_12_LFN_STRUCT

    def _get_entry_struct(self):
        return FAT_12_ENTRY_STRUCT

    def _get_entry_size(self):
        return FAT12_ENTRY_SIZE


class FAT12Reader(FATReader):
    def __init__(self, reader):
        super().__init__(reader)

        self.boot_sector = self.read_bs()

        self.fats_offset = self.boot_sector.BytesPerSector
        self.fats = [
            FAT12Table(
                self.reader,
                self.fats_offset + i * self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector,
                self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector
            ) for i in range(self.boot_sector.FATCopies)
        ]
        self.root_dir_offset = self.fats_offset + self.boot_sector.FATCopies * self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector
        self.data_offset = self.root_dir_offset + self.boot_sector.MaxRootEntries * FAT12_ENTRY_SIZE
        self.cluster_size = self.boot_sector.BytesPerSector * self.boot_sector.SectorsPerCluster

        self.root_dir = FAT12Dir(
            self.fats[0],
            self.reader, self.reader,
            self.root_dir_offset,
            self.boot_sector.MaxRootEntries * FAT12_ENTRY_SIZE,
            self.cluster_size,
            self.data_offset
        )

    def read_bs(self):
        return FAT12_STRUCT(
            *(
                self.reader.unpack(unpack_str, size, offset)[0]
                for offset, size, _, unpack_str in FAT12_SIGN
            )
        )

    @property
    def root(self):
        return self.root_dir
