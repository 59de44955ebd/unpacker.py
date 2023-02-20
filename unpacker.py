import os
import re
import shutil
import sys
import zlib

DEV_NULL = 'nul' if sys.platform == 'win32' else '/dev/null'

def unpack(f, dest_dir=None, do_decompile=False):
    if not os.path.exists(f):
        return print('Error: file does not exist.')

    os.environ['PATH'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', sys.platform) + os.pathsep + os.environ['PATH']

    fn = os.path.basename(f)
    bn, ext = os.path.splitext(fn)

    if os.path.isdir(f) and ext == '.app':  # macOS projector.app bundle?
        fn_bin = os.path.join(f, 'Contents', 'MacOS', bn)
        bin_file = None
        if os.path.isdir(fn_bin):
            bin_file = fn_bin
        else:
            l = os.listdir(os.path.join(f, 'Contents', 'MacOS'))
            if len(l):
                bin_file = os.path.join(f, 'Contents', 'MacOS', l[0])
        if bin_file is not None:
            print(f'Unpacking Mac OS X/macOS projector "{fn}"...')
            output_dir = os.path.join(dest_dir if dest_dir else os.path.dirname(f), bn + '_contents')
            if os.path.isdir(output_dir):
                shutil.rmtree(output_dir)
            os.mkdir(output_dir)
            return unpack_projector(bin_file, output_dir, do_decompile)

    elif ext == '.exe':  # Windows projector.exe?
        print(f'Unpacking Windows projector "{fn}"...')
        output_dir = os.path.join(dest_dir if dest_dir else os.path.dirname(f), bn + '_contents')
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        return unpack_projector(f, output_dir, do_decompile)

    # check if it's an old Mac OS 9- 68k/PPC/FAT binary
    with open(f, 'rb') as fh:
        magic = fh.read(4)
    is_macos_bin = magic[:2] == b'PJ' or magic[2:] == b'JP'
    if not is_macos_bin:
        MAGIC_MACOS = [
            b'Joy!',              # D10- mac projector
            b'\xCA\xFE\xBA\xBE',  # D11+ Projector Resource
            b'\xCE\xFA\xED\xFE',  # D11+ Projector Intel Resource
            b'RIFX'               # data fork of classic mac app
        ]
        for m in MAGIC_MACOS:
            if magic == m:
                is_macos_bin = True
                break
    if is_macos_bin:
        print(f'Unpacking Mac OS projector "{fn}"...')
        output_dir = os.path.join(dest_dir if dest_dir else os.path.dirname(f), bn + '_contents')
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        return unpack_projector(f, output_dir, do_decompile)

    print('Error: File not supported.')

def unpack_projector (exe_file, output_dir, do_decompile=False):
    with open(exe_file, 'rb') as fh:
        data_full = fh.read()

    m1 = re.search(b'RIFX([\x00-\xFF]{4})APPL', data_full)
    m2 = re.search(b'XFIR([\x00-\xFF]{4})LPPA', data_full)

    if m1 and m2:
        start_pos = m1.start() if m1.start() < m2.start() else m2.start()
        byteorder = 'big' if m1.start() < m2.start() else 'little'
    elif m1:
        start_pos = m1.start()
        byteorder = 'big'
    elif m2:
        start_pos = m2.start()
        byteorder = 'little'
    else:
        return print(f'Error: Could not identify "{exe_file}" as Director projector.')

    offset = 32
    data_full = data_full[offset:]
    exe_size = len(data_full)

    # find RIFX/XFIR and RIFF chunks
    res = []
    res2 = []
    xres = []

    start_pos += 12

    data = data_full[start_pos:]

    if byteorder == 'big':
        for m in re.finditer(b'RIFX([\x00-\xFF]{4})(MV93|MC95)', data):
            res.append([m.start(), m.group()[8:]])
        for m in re.finditer(b'RIFX([\x00-\xFF]{4})(FGDM|FGDC)', data):
            res2.append([m.start(), m.group()[8:]])
    else:
        for m in re.finditer(b'XFIR([\x00-\xFF]{4})(39VM|59CM)', data):
            res.append([m.start(), m.group()[8:]])
        for m in re.finditer(b'XFIR([\x00-\xFF]{4})(MDGF|CDGF)', data):
            res2.append([m.start(), m.group()[8:]])

    for m in re.finditer(b'RIFF([\x00-\xFF]{4})XtraFILE', data):
        xres.append(m.start())

    if len(res) == 0:
        if len(res2) == 0:
            return print('Nothing found to extract!')
        else:
            compressed = True
            res = res2
    else:
        compressed = False

    # header template
    header = ((b'RIFX' if byteorder == 'big' else b'XFIR') +
            int.to_bytes(exe_size - 8 + offset, 4, byteorder) +
            (b'MV93imap' if byteorder == 'big' else b'39VMpami') +
            int.to_bytes(24, 4, byteorder) +
            int.to_bytes(1, 4, byteorder))

    # extract file names from Dict chunk
    dir_names = []
    x32_names = []

    pos = res[0][0]  # position of first XFIR/RIFX

    # find last 'Dict' (littleEndian: 'tciD') before this position
    m = None
    for m in re.finditer(b'Dict' if byteorder == 'big' else b'tciD', data[:pos-3]):
        pass

    if m:
        dict = data[m.start():pos]
        cnt = int.from_bytes(dict[24:28], byteorder)

        # no idea what's going on here
        if cnt > 0xFFFF:
            cnt = int.from_bytes(dict[24:28], 'little' if byteorder == 'big' else 'big')

        if cnt == 1:
            # finding actual original filename would require parsing .dir file, so we use the projector name instead
            bn, _ = os.path.splitext(os.path.basename(exe_file))
            dir_names.append(bn + '.dxr')
        else:
            pt = cnt * 8 + 64
            for i in range(cnt):
                flen = int.from_bytes(dict[pt:pt+4], byteorder)
                fn = dict[pt + 4:pt + 4 + flen]
                if b'Xtras:' in fn or fn.endswith(b' Xtra') or fn.endswith(b'.x32') or fn.endswith(b'.cpio'):
                    x32_names.append(get_filename(fn.decode()))
                else:
                    dir_names.append(get_filename(fn.decode()))
                if i < cnt - 1:
                    pt += 4 + flen + (4 - flen % 4 if flen % 4 else 0)

    if compressed:  # compressed files
        print('Notice: files in projector are compressed.')

        file_num = 0
        for r in res:
            pos = r[0]
            fn = dir_names[file_num]
            file_num += 1

            _, ext = os.path.splitext(fn)
            if ext == '':
                fn += '.dcr'  # just guessing
            else:
                fn = fn[:-4] + ('.cct' if ext == '.cst' else '.dcr')

            chunk_size = int.from_bytes(data[pos + 4:pos + 8], byteorder)

            fn = os.path.join(output_dir, sanitize_filename(fn))
            with open(fn, 'wb') as fh:
                fh.write(data[pos:pos + chunk_size + 8])

            if do_decompile:
                decompile(fn)
            rebuild(fn)

    else:  # non-compressed files
        print('Notice: files in projector are not compressed.')

        file_num = 0
        for r in res:
            pos = r[0] + 32 + offset
            fn = dir_names[file_num]
            file_num += 1

            _, ext = os.path.splitext(fn)
            if ext == '':  # just guessing
                fn += '.dxr'
            else:
                fn = fn[:-4] + ('.cxt' if ext == '.cst' else '.dxr')

            fn = os.path.join(output_dir, sanitize_filename(fn))
            with open(fn, 'wb') as fh:
                fh.write(header)
                fh.write(int.to_bytes(start_pos + pos + 12, 4, byteorder))
                fh.write(int.to_bytes(1923, 4, byteorder))
                fh.write(data_full)

            if do_decompile:
                decompile(fn)
            rebuild(fn)

    # extract xtras
    file_num = 0
    for pos in xres:
        chunk_size = int.from_bytes(data[pos:pos+4], 'big')  # always bigEndian!
        xdata = data[pos + 48:pos + 48 + chunk_size]
        fn = x32_names[file_num]
        file_num += 1
        xdata = zlib.decompress(xdata)
        with open(os.path.join(output_dir, sanitize_filename(fn)), 'wb') as fh:
            fh.write(xdata)

    print(f'Done. {len(res) + len(xres)} files were extracted to "{output_dir}".')

def rebuild(fn):
    dest_file = fn + '.tmp'
    os.system(f'ProjectorRays --rebuild-only "{fn}" "{dest_file}" >{DEV_NULL}')
    if os.path.isfile(dest_file):
        os.unlink(fn)
        os.rename(dest_file, fn)

def decompile(fn):
    dest_file, ext = os.path.splitext(fn)
    dest_file += ('_decompiled.cst' if ext == '.cxt' or ext == '.cct' else '_decompiled.dir')
    os.system(f'ProjectorRays "{fn}" "{dest_file}" >{DEV_NULL}')

def get_filename(fn):
    ''' cross-platform, extracts filename of Windows, POSIX or Mac OS path '''
    if "/" in fn:
        pd = "/"  # POSIX (macOS/Mac OS X)
    elif "\\" in fn:
        pd = "\\"  # Windows
    else:
        pd = ":"  # Mac OS
    return fn.split(pd)[-1]

def sanitize_filename(fn):
    for c in r'\/:*?"<>|':
	    fn = fn.replace(c, '_')
    return fn


if __name__ == '__main__':
    args = sys.argv[1:]
    do_decompile = '-decompile' in args
    if do_decompile:
        args.remove('-decompile')
    if len(args):
        unpack(args[0], do_decompile=do_decompile)
    else:
        print('Usage: python unpacker.py [-decompile] <projector-file>')
