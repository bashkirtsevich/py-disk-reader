from collections import namedtuple

from .fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir, FATBootSector
from .signatures import *

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
    @staticmethod
    def _get_entry_reader_class():
        return FAT16EntryReader

    @staticmethod
    def _get_dir_entry_class():
        return FAT16Dir


class FAT16Dir(FATDir):
    @staticmethod
    def _get_entry_perms():
        return FAT16_ENTRY_PERMS

    @staticmethod
    def _get_lfn():
        return FAT16_LFN

    @staticmethod
    def _get_entry():
        return FAT16_ENTRY

    @staticmethod
    def _get_entry_class():
        return FAT16Entry

    @staticmethod
    def _get_lfn_struct():
        return FAT16_LFN_STRUCT

    @staticmethod
    def _get_entry_struct():
        return FAT16_ENTRY_STRUCT

    @staticmethod
    def _get_entry_size():
        return FAT16_ENTRY_SIZE


class FAT16BootSector(FATBootSector):
    @property
    def max_root_entries(self):
        return self.data.MaxRootEntries  # FIXME: Same as in FAT12

    @property
    def root_size(self):
        return self.max_root_entries * FAT16_ENTRY_SIZE

    @property
    def root_dir_offset(self):
        return self.fats_offset + self.fats_copies * self.fat_size  # FIXME: Same as in FAT12

    @property
    def data_offset(self):
        return super().data_offset + self.root_size  # FIXME: Same as in FAT12

    @staticmethod
    def _get_sign():
        return FAT16_SIGN

    @staticmethod
    def _get_struct_class():
        return FAT16_STRUCT


class FAT16Reader(FATReader):
    def read_root(self):
        return FAT16Dir(  # FIXME: Same as in FAT12
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
        return FAT16BootSector

    @staticmethod
    def _get_fat_table_class():
        return FAT16Table
