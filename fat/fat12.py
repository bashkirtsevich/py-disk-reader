from collections import namedtuple

from .fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir
from .signatures import *

FAT12_STRUCT = namedtuple("FAT12", (it[2] for it in FAT12_SIGN))
FAT12_ENTRY_STRUCT = namedtuple("FAT12Directory", (it[2] for it in FAT12_ENTRY))
FAT12_LFN_STRUCT = namedtuple("FAT12LFN", (it[2] for it in FAT12_LFN))


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


class FAT12EntryReader(FATEntryReader):
    pass


class FAT12Entry(FATEntry):
    @staticmethod
    def _get_entry_reader_class():
        return FAT12EntryReader

    @staticmethod
    def _get_dir_entry_class():
        return FAT12Dir


class FAT12Dir(FATDir):
    @staticmethod
    def _get_entry_perms():
        return FAT12_ENTRY_PERMS

    @staticmethod
    def _get_lfn():
        return FAT12_LFN

    @staticmethod
    def _get_entry():
        return FAT12_ENTRY

    @staticmethod
    def _get_entry_class():
        return FAT12Entry

    @staticmethod
    def _get_lfn_struct():
        return FAT12_LFN_STRUCT

    @staticmethod
    def _get_entry_struct():
        return FAT12_ENTRY_STRUCT

    @staticmethod
    def _get_entry_size():
        return FAT12_ENTRY_SIZE


class FAT12Reader(FATReader):
    def __init__(self, reader):
        super().__init__(reader)

        self.boot_sector = self.read_bs()

        # self.fats_offset = self.boot_sector.BytesPerSector
        self.fats_offset = self.boot_sector.SectorsCount * self.boot_sector.BytesPerSector
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
