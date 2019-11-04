from fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir
from signatures import *

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
