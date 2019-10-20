from collections import namedtuple

FAT12_SIGN = (
    # ( offset, size, name, unpack string)
    (0x00, 3, 'JumpInstruction', '3s'),
    (0x03, 8, 'OemID', '8s'),
    (0x0B, 2, 'BytesPerSector', '<H'),
    (0x0D, 1, 'SectorsPerCluster', 'B'),
    (0x0E, 2, 'SectorsCount', '<H'),
    (0x10, 1, 'FATCopies', 'B'),
    (0x11, 2, 'MaxRootEntries', '<H'),
    (0x13, 2, 'TotalSectors', '<H'),
    (0x15, 1, 'MediaDescriptor', 'B'),
    (0x16, 2, 'SectorsPerFAT', '<H'),  # DWORD in FAT32
    (0x18, 2, 'SectorsPerTrack', '<H'),
    (0x1A, 2, 'Heads', '<H'),
    (0x1C, 4, 'HiddenSectors', '<I'),  # Here differs from FAT32
    (0x20, 4, 'TotalLogicalSectors', '<I'),
    (0x24, 1, 'PhysDriveNumber', 'B'),
    (0x25, 1, 'CurrentHead', 'B'),
    (0x26, 1, 'Signature', 'B'),  # (0x28 or (0x29
    (0x27, 4, 'VolumeID', '<I'),
    (0x2B, 11, 'VolumeLabel', '11s'),
    (0x36, 8, 'FSType', '8s'),
    (0x3E, 448, 'BootLoader', '448s'),
    (0x1FE, 2, 'BootSignature', '<H')  # 55 AA
)

FAT12_ENTRY_PERMS = (0x0B, 1, 'B')

FAT_12_ENTRY = (
    (0x00, 8, 'Name', '8s'),
    (0x08, 3, 'Ext', '3s'),
    (0x0B, 1, 'DOSPerms', 'B'),
    (0x0C, 1, 'Flags', 'B'),  # bit 3/4 set: lowercase basename/extension (NT)
    (0x0D, 1, 'Reserved', 'B'),  # creation time fine resolution in 10 ms units, range 0-199
    (0x0E, 2, 'CTime', '<H'),
    (0x10, 2, 'CDate', '<H'),
    (0x12, 2, 'ADate', '<H'),
    (0x14, 2, 'ClusterHi', '<H'),
    (0x16, 2, 'MTime', '<H'),
    (0x18, 2, 'MDate', '<H'),
    (0x1A, 2, 'ClusterLo', '<H'),
    (0x1C, 4, 'FileSize', '<I')
)
FAT_12_ENTRY_SIZE = 32

FAT12_LFN = (
    (0x00, 1, 'SeqNumber', 'B'),  # LFN slot #
    (0x01, 10, 'Name5', '10s'),
    (0x0B, 1, 'DOSPerms', 'B'),  # always 0xF
    (0x0C, 1, 'Type', 'B'),  # always zero in VFAT LFN
    (0x0D, 1, 'Checksum', 'B'),
    (0x0E, 12, 'Name6', '12s'),
    (0x1A, 2, 'ClusterLo', '<H'),  # always zero
    (0x1C, 4, 'Name2', '4s')
)

FAT16_SIGN = FAT12_SIGN

FAT16_STRUCT = namedtuple("FAT16", [it[2] for it in FAT16_SIGN])

FAT_32_SIGN = (
    (0x00, 'chJumpInstruction', '3s'),
    (0x03, 'chOemID', '8s'),
    (0x0B, 'wBytesPerSector', '<H'),
    (0x0D, 'uchSectorsPerCluster', 'B'),
    (0x0E, 'wSectorsCount', '<H'),  # reserved sectors (min 32?)
    (0x10, 'uchFATCopies', 'B'),
    (0x11, 'wMaxRootEntries', '<H'),
    (0x13, 'wTotalSectors', '<H'),
    (0x15, 'uchMediaDescriptor', 'B'),
    (0x16, 'wSectorsPerFAT', '<H'),  # not used, see 24h instead
    (0x18, 'wSectorsPerTrack', '<H'),
    (0x1A, 'wHeads', '<H'),
    (0x1C, 'wHiddenSectors', '<H'),
    (0x1E, 'wTotalHiddenSectors', '<H'),
    (0x20, 'dwTotalLogicalSectors', '<I'),
    (0x24, 'dwSectorsPerFAT', '<I'),
    (0x28, 'wMirroringFlags', '<H'),  # bits 0-3: active FAT, it bit 7 set; else: mirroring as usual
    (0x2A, 'wVersion', '<H'),
    (0x2C, 'dwRootCluster', '<I'),  # usually 2
    (0x30, 'wFSISector', '<H'),  # usually 1
    (0x32, 'wBootCopySector', '<H'),  # 0x0000 or 0xFFFF if unused, usually 6
    (0x34, 'chReserved', '12s'),
    (0x40, 'chPhysDriveNumber', 'B'),
    (0x41, 'chFlags', 'B'),
    (0x42, 'chExtBootSignature', 'B'),
    (0x43, 'dwVolumeID', '<I'),
    (0x47, 'sVolumeLabel', '11s'),
    (0x52, 'sFSType', '8s'),
    # ~ 0x72, 'chBootstrapCode', '390s'),
    (0x1FE, 'wBootSignature', '<H')  # 55 AA
)
