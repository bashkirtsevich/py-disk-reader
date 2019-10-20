# Python low-level disk reader

TL;DR: Python implementation for low-level disk (and disk images) reading, parse MBR, file systems, etc.

# Examples

## FAT12

```python
from hashlib import sha1

with open("images/floppy2.img", "rb") as f:
    img = FAT12Reader(FileReader(f))

    files = list(img.root_dir)
    
    bar = files[1]
    baz = bar.read()
    print(bar.name, sha1(baz).hexdigest(), baz)

    bar = files[6]
    for i, n in enumerate(bar):
        print(i, n.name)
```