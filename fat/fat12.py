from collections import namedtuple

from .fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir, FATBootSector
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


class FAT12BootSector(FATBootSector):
    @property
    def max_root_entries(self):
        return self.data.MaxRootEntries

    @property
    def root_size(self):
        return self.max_root_entries * FAT12_ENTRY_SIZE

    @property
    def root_dir_offset(self):
        return self.fats_offset + self.fats_copies * self.fat_size

    @property
    def data_offset(self):
        return super().data_offset + self.root_size

    @staticmethod
    def _get_sign():
        return FAT12_SIGN

    @staticmethod
    def _get_struct_class():
        return FAT12_STRUCT


class FAT12Reader(FATReader):
    def read_root(self):
        return FAT12Dir(
            self.primary_fat,
            self.reader,
            self.reader,
            self.boot_sector.root_dir_offset,
            self.boot_sector.root_size,
            self.boot_sector.cluster_size,
            self.boot_sector.data_offset
        )

    @staticmethod
    def _get_boot_sector_class():
        return FAT12BootSector

    @staticmethod
    def _get_fat_table_class():
        return FAT12Table
