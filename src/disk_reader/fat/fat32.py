from struct import unpack
from collections import namedtuple
from disk_reader.fat import (
    FATTable,
    FATEntryReader,
    FATReader,
    FATEntry,
    FATDir,
    FATBootSector
)
from disk_reader.fat.signatures import (
    FAT32_SIGN,
    FAT32_ENTRY_PERMS,
    FAT32_ENTRY,
    FAT32_LFN,
    FAT32_ENTRY_SIZE
)
from disk_reader.utils import slice_len


FAT32_STRUCT = namedtuple("FAT32", (it[2] for it in FAT32_SIGN))
FAT32_ENTRY_STRUCT = namedtuple("FAT32Directory", (it[2] for it in FAT32_ENTRY))
FAT32_LFN_STRUCT = namedtuple("FAT32LFN", (it[2] for it in FAT32_LFN))


class FAT32Table(FATTable):
    FAT32_ENTRY_START = 0x00000002
    FAT32_ENTRY_END = 0x0FFFFFEF

    def _get(self, idx):
        return int.from_bytes(
            self.reader.read(4, idx * 4, self.base_ptr),
            "little"
        )

    def _validate_idx(self, idx):
        if idx * 4 > self.size:
            # TODO: Make OutOfBoundsException
            raise Exception("Out of bounds")

    def _is_eof(self, val):
        # FIXME: Use DeMorgan rule
        return not (self.FAT32_ENTRY_START <= val <= self.FAT32_ENTRY_END)


class FAT32EntryReader(FATEntryReader):
    pass


class FAT32Entry(FATEntry):
    @staticmethod
    def _get_entry_reader_class():
        return FAT32EntryReader

    @staticmethod
    def _get_dir_entry_class():
        return FAT32Dir


class FAT32Dir(FATDir):
    @staticmethod
    def _get_entry_perms():
        return FAT32_ENTRY_PERMS

    @staticmethod
    def _get_lfn():
        return FAT32_LFN

    @staticmethod
    def _get_entry():
        return FAT32_ENTRY

    @staticmethod
    def _get_entry_class():
        return FAT32Entry

    @staticmethod
    def _get_lfn_struct():
        return FAT32_LFN_STRUCT

    @staticmethod
    def _get_entry_struct():
        return FAT32_ENTRY_STRUCT

    @staticmethod
    def _get_entry_size():
        return FAT32_ENTRY_SIZE


class FAT32BootSector(FATBootSector):
    @property
    def root_cluster(self):
        return self.data.RootCluster

    @staticmethod
    def _get_sign():
        return FAT32_SIGN

    @staticmethod
    def _get_struct_class():
        return FAT32_STRUCT


class FAT32Reader(FATReader):
    def read_root(self):
        root_reader = FAT32EntryReader(
            self.reader,
            self.primary_fat,
            self.boot_sector.root_cluster,
            self.boot_sector.cluster_size,
            self.boot_sector.data_offset
        )
        return FAT32Dir(
            self.primary_fat,
            self.reader,
            root_reader,
            0,
            root_reader.size(),
            self.boot_sector.cluster_size,
            self.boot_sector.data_offset
        )

    @staticmethod
    def _get_boot_sector_class():
        return FAT32BootSector

    @staticmethod
    def _get_fat_table_class():
        return FAT32Table
