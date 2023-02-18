import os
import shutil
from unpacker import unpack

PATH = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':

    dest_dir = os.path.join(PATH, 'test_files_unpacked')
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    os.mkdir(dest_dir)

    test_files = list(os.listdir(os.path.join(PATH, 'test_files')))
    for fn in test_files:
        try:
            unpack(os.path.join(PATH, 'test_files', fn), dest_dir=dest_dir, do_decompile=True)
        except Exception as e:
            print('[ERROR]', e)
        print()
