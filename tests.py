import logging
import os
import shutil
import colorama as c
from unpacker import unpack

if __name__ == '__main__':
    PATH = os.path.dirname(os.path.realpath(__file__))
    logging.basicConfig(level = logging.INFO, format = '[%(levelname)s] %(message)s')
    c.init()

    dest_dir = os.path.join(PATH, 'test_files_unpacked')
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    os.mkdir(dest_dir)

    test_files = list(os.listdir(os.path.join(PATH, 'test_files')))
    failed = 0
    for fn in test_files:
        try:
            output_dir, num_dirs, num_xtras = unpack(os.path.join(PATH, 'test_files', fn), dest_dir=dest_dir, do_decompile=True)
            print(f'{c.Fore.LIGHTGREEN_EX}Done. {num_dirs+num_xtras} files were extracted to "{output_dir}".{c.Fore.RESET}')
        except Exception as e:
            print(f'{c.Fore.RED}[ERROR] {e}{c.Fore.RESET}')
            failed += 1
        print()

    if failed == 0:
        print(f'{c.Fore.LIGHTGREEN_EX}All {len(test_files)} projectors were successfully unpacked!{c.Fore.RESET}')
    else:
        print(f'{c.Fore.RED}{failed} of {len(test_files)} projectors could not be unpacked.{c.Fore.RESET}')
