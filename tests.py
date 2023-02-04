import os
import shutil
import time
from unpacker import unpack

PATH = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':

    dest_dir = os.path.join(PATH, 'test_files_unpacked')
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
#        time.sleep(.5)
    os.mkdir(dest_dir)

    test_files = list(os.listdir(os.path.join(PATH, 'test_files')))
    for fn in test_files:
#        print(os.path.join(PATH, 'test_files', fn))
        unpack(os.path.join(PATH, 'test_files', fn), dest_dir)
        print()
