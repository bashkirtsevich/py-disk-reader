from struct import unpack

from fat import FATTable, FATEntryReader, FATReader, FATEntry, FATDir
from signatures import *
from utils import slice_len

SECTOR_SIZE = 512

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
    def _create_entry_reader(self):
        return FAT32EntryReader(
            self.basic_reader,
            self.table,
            self.params.ClusterHi << 16 | self.params.ClusterLo,
            self.cluster_size,
            self.data_ptr
        )

    def _create_dir_entry(self):
        return FAT32Dir(
            self.table,
            self.basic_reader,
            self.entry_reader,
            0,
            self.entry_reader.size(),
            self.cluster_size,
            self.data_ptr
        )


class FAT32Dir(FATDir):
    def _parse_entry(self, data):
        offset, size, unpack_str = FAT32_ENTRY_PERMS

        return FAT32_LFN_STRUCT(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in FAT32_LFN)
        ) if unpack(unpack_str, data[slice_len(offset, size)])[0] == 0xF else FAT32_ENTRY_STRUCT(
            *(unpack(unpack_str, data[slice_len(offset, size)])[0]
              for offset, size, _, unpack_str in FAT32_ENTRY)
        )

    def _get_entry_class(self):
        return FAT32Entry

    def _get_lfn_struct(self):
        return FAT32_LFN_STRUCT

    def _get_entry_struct(self):
        return FAT32_ENTRY_STRUCT

    def _get_entry_size(self):
        return FAT32_ENTRY_SIZE


class FAT32Reader(FATReader):
    def __init__(self, reader):
        super().__init__(reader)

        self.boot_sector = self.read_bs()

        self.fats_offset = self.boot_sector.SectorsCount * self.boot_sector.BytesPerSector
        self.fats = [
            FAT32Table(
                self.reader,
                self.fats_offset + i * self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector,
                self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector
            ) for i in range(self.boot_sector.FATCopies)
        ]
        self.data_offset = self.fats_offset + self.boot_sector.FATCopies * self.boot_sector.SectorsPerFAT * self.boot_sector.BytesPerSector
        self.cluster_size = self.boot_sector.BytesPerSector * self.boot_sector.SectorsPerCluster

        root_reader = FAT32EntryReader(
            self.reader,
            self.fats[0],
            self.boot_sector.RootCluster,
            self.cluster_size,
            self.data_offset
        )
        self.root_dir = FAT32Dir(
            self.fats[0],
            self.reader,
            root_reader,
            0,
            root_reader.size(),
            self.cluster_size,
            self.data_offset
        )

    def read_bs(self):
        return FAT32_STRUCT(
            *(
                self.reader.unpack(unpack_str, size, offset)[0]
                for offset, size, _, unpack_str in FAT32_SIGN
            )
        )

    @property
    def root(self):
        return self.root_dir
