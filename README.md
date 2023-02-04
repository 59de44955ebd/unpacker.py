# unpacker.py
Simple python 3 script for extracting movies, castlibs and xtras from Macromedia/Adobe Director projectors

This script allows to unpack Director files (movies, castlibs and xtras) included in Director projectors.
It supports Director versions 4 to 12 and the following flavors:

* Windows projector (.exe), 16-bit
* Windows projector (.exe), 32-bit
* Mac OS 9- projectors (data fork), 68k/PPC/FAT
* Mac OS X projectors (Intel/PPC/Universal)
* macOS projectors (.app bundle, Intel)

## Usage

```
$ python unpacker.py <projector-file>
```

## Tests

Running

```
$ python tests.py
```

will unpack the 27 example projectors found in "test_files" to a new folder "test_files_unpacked".

## Notes

Director movies and castlibs extracted from projectors are always protected/compressed. You can try to decompile such files with [ProjectorRays](https://github.com/ProjectorRays/ProjectorRays) to turn them into editable files that can be opened and edited in Director.
