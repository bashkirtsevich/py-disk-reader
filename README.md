# Python low-level disk reader

TL;DR: Python implementation for low-level disk (and disk images) reading, parse MBR, file systems, etc.


# Installation
py-disk-reader is temporarily unavailable on PyPI. 

Use github link to install:
```
pip install git+https://github.com/bashkirtsevich/py-disk-reader
```
# Examples

## FAT12

```python
from hashlib import sha1
from disk_reader import FAT12Reader
from disk_reader.reader import FileReader

with open("images/floppy2.img", "rb") as f:
    img = FAT12Reader(FileReader(f))

    files = list(img.root_dir)

    for i, n in enumerate(files):
        print(i, n.name)

    bar = files[1]
    baz = bar.read()
    print(bar.name, sha1(baz).hexdigest(), baz)

    print("----")

    bar = list(files[6])
    for i, n in enumerate(bar):
        print(i, n.name)

    baz = bar[7].read()
    print(bar[7].name, sha1(baz).hexdigest(), baz)

```

## FAT16

```python
from hashlib import sha1
from disk_reader import FAT16Reader
from disk_reader.reader import FileReader

with open("images/fat16.img", "rb") as f:
    img = FAT16Reader(FileReader(f))

    files = list(img.root_dir)

    for i, n in enumerate(files):
        print(i, n.name)

    bar = files[15]
    baz = bar.read()
    print(bar.name, sha1(baz).hexdigest(), baz)

    print("----")

    bar = list(files[0])
    for i, n in enumerate(bar):
        print(i, n.name)

    baz = bar[3].read()
    print(bar[3].name, sha1(baz).hexdigest(), baz)

```

## FAT32

```python
from hashlib import sha1
from disk_reader import FAT32Reader
from disk_reader.reader import FileReader

with open("images/fat32.img", "rb") as f:
    img = FAT32Reader(FileReader(f))

    files = list(img.root_dir)

    for i, n in enumerate(files):
        print(i, n.name)

    bar = files[3]
    baz = bar.read()
    print(bar.name, sha1(baz).hexdigest(), baz)

    bar = list(files[1])
    for i, n in enumerate(bar):
        print(i, n.name)

    baz = bar[3].read()
    print(bar[3].name, sha1(baz).hexdigest(), baz)

```