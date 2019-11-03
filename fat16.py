from struct import unpack

from fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir
from signatures import *
from utils import slice_len

SECTOR_SIZE = 512

FAT16_STRUCT = namedtuple("FAT16", (it[2] for it in FAT16_SIGN))
FAT16_ENTRY_STRUCT = namedtuple("FAT16Directory", (it[2] for it in FAT16_ENTRY))
FAT16_LFN_STRUCT = namedtuple("FAT16LFN", (it[2] for it in FAT16_LFN))


class FAT16Table(FATTable):
    FAT16_ENTRY_START = 0x0002
    FAT16_ENTRY_END = 0xFFEF

    def _get(self, idx):
        return int.from_bytes(
            self.reader.read(4, idx * 2, self.base_ptr),
            "little"
        )

    def _validate_idx(self, idx):
        if idx * 4 > self.size:
            # TODO: Make OutOfBoundsException
            raise Exception("Out of bounds")

    def _is_eof(self, val):
        # FIXME: Use DeMorgan rule
        return not (self.FAT16_ENTRY_START <= val <= self.FAT16_ENTRY_END)


class FAT16EntryReader(FATEntryReader):
    pass


class FAT16Entry(FATEntry):
    def _create_entry_reader(self):
        return FAT16EntryReader(
            self.basic_reader,
            self.table,
            self.params.ClusterHi << 16 | self.params.ClusterLo,
            self.cluster_size,
            self.data_ptr
        )

    def _create_dir_entry(self):
        return FAT16Dir(
            self.table,
            self.basic_reader,
            self.entry_reader,
            0,
            self.entry_reader.size(),
            self.cluster_size,
            self.data_ptr
        )


class FAT16Dir(FATDir):
    def _parse_entry(self, data):
        offset, size, unpack_str = FAT16_ENTRY_PERMS

        return FAT16_LFN_STRUCT(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in FAT16_LFN)
        ) if unpack(unpack_str, data[slice_len(offset, size)])[0] == 0xF else FAT16_ENTRY_STRUCT(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in FAT16_ENTRY)
        )

    def _get_entry_class(self):
        return FAT16Entry

    def _get_lfn_struct(self):
        return FAT16_LFN_STRUCT

    def _get_entry_struct(self):
        return FAT16_ENTRY_STRUCT

    def _get_entry_size(self):
        return FAT16_ENTRY_SIZE


class FAT16Reader(FATReader):
    def __init__(self, reader):
        super().__init__(reader)

        self.boot_sector = self.read_bs()

        self.fats_offset = self.boot_sector.SectorsCount * self.boot_sector.BytesPerSector
        self.fats = [
            FAT16Table(
                self.reader,
                self.fats_offset + i * self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector,
                self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector
            ) for i in range(self.boot_sector.FATCopies)
        ]
        self.root_dir_offset = self.fats_offset + self.boot_sector.FATCopies * self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector
        self.data_offset = self.root_dir_offset + self.boot_sector.MaxRootEntries * FAT12_ENTRY_SIZE
        self.cluster_size = self.boot_sector.BytesPerSector * self.boot_sector.SectorsPerCluster

        self.root_dir = FAT16Dir(
            self.fats[0],
            self.reader, self.reader,
            self.root_dir_offset,
            self.boot_sector.MaxRootEntries * FAT12_ENTRY_SIZE,
            self.cluster_size,
            self.data_offset
        )

    def read_bs(self):
        return FAT16_STRUCT(
            *(
                self.reader.unpack(unpack_str, size, offset)[0]
                for offset, size, _, unpack_str in FAT16_SIGN
            )
        )

    @property
    def root(self):
        return self.root_dir
