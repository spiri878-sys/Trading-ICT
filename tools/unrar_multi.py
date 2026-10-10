# Extract a multi-volume RAR via libarchive's archive_read_open_filenames (ctypes).
import ctypes, sys, os
la = ctypes.CDLL("libarchive.so.13")
la.archive_read_new.restype = ctypes.c_void_p
la.archive_error_string.restype = ctypes.c_char_p
la.archive_entry_pathname.restype = ctypes.c_char_p
la.archive_entry_size.restype = ctypes.c_int64
outdir, vols = sys.argv[1], sys.argv[2:]
a = la.archive_read_new()
la.archive_read_support_format_all(ctypes.c_void_p(a)); la.archive_read_support_filter_all(ctypes.c_void_p(a))
arr = (ctypes.c_char_p * (len(vols)+1))(*[v.encode() for v in vols], None)
r = la.archive_read_open_filenames(ctypes.c_void_p(a), arr, ctypes.c_size_t(10240))
if r != 0: sys.exit("open: %s" % la.archive_error_string(ctypes.c_void_p(a)))
entry = ctypes.c_void_p()
buf = ctypes.create_string_buffer(1 << 20)
while la.archive_read_next_header(ctypes.c_void_p(a), ctypes.byref(entry)) == 0:
    name = la.archive_entry_pathname(entry).decode(); size = la.archive_entry_size(entry)
    out = os.path.join(outdir, os.path.basename(name)); n = 0
    with open(out, "wb") as f:
        while True:
            k = la.archive_read_data(ctypes.c_void_p(a), buf, ctypes.c_size_t(len(buf)))
            if k < 0: sys.exit("read: %s" % la.archive_error_string(ctypes.c_void_p(a)))
            if k == 0: break
            f.write(buf.raw[:k]); n += k
    print(name, "declared", size, "written", n, "OK" if n == size else "MISMATCH")
