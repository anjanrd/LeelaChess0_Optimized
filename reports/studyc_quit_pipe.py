"""Send UCI stop/quit through the running worker's sole writable pipe."""
import ctypes as c
from ctypes import wintypes as w

WORKER = 31924
ENGINE = 13124
k = c.WinDLL('kernel32', use_last_error=True)
nt = c.WinDLL('ntdll')
k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.GetCurrentProcess.restype = w.HANDLE
k.DuplicateHandle.argtypes = [w.HANDLE, w.HANDLE, w.HANDLE, c.POINTER(w.HANDLE), w.DWORD, w.BOOL, w.DWORD]
k.GetFileType.argtypes = [w.HANDLE]
k.GetFileType.restype = w.DWORD
k.WriteFile.argtypes = [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p]
k.CloseHandle.argtypes = [w.HANDLE]
k.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
k.GetExitCodeProcess.argtypes = [w.HANDLE, c.POINTER(w.DWORD)]
nt.NtQuerySystemInformation.argtypes = [w.ULONG, c.c_void_p, w.ULONG, c.POINTER(w.ULONG)]
nt.NtQuerySystemInformation.restype = c.c_long

class Entry(c.Structure):
    _fields_ = [('Object', c.c_void_p), ('ProcessId', c.c_size_t), ('Handle', c.c_size_t), ('Access', w.ULONG), ('Trace', w.USHORT), ('Type', w.USHORT), ('Attributes', w.ULONG), ('Reserved', w.ULONG)]

size = 1024 * 1024
while True:
    buf = c.create_string_buffer(size)
    required = w.ULONG()
    status = nt.NtQuerySystemInformation(64, buf, size, c.byref(required))
    if status == 0:
        break
    assert status & 0xffffffff == 0xc0000004, hex(status & 0xffffffff)
    size = max(size * 2, required.value + 65536)
owner = k.OpenProcess(0x40, False, WORKER)
assert owner, c.get_last_error()
handles = []
try:
    count = c.c_size_t.from_buffer(buf).value
    for index in range(count):
        e = Entry.from_buffer(buf, 2 * c.sizeof(c.c_size_t) + index * c.sizeof(Entry))
        if e.ProcessId != WORKER or not e.Access & 2:
            continue
        dup = w.HANDLE()
        if k.DuplicateHandle(owner, w.HANDLE(e.Handle), k.GetCurrentProcess(), c.byref(dup), 0, False, 2):
            if k.GetFileType(dup) == 3:
                print(f'Worker {WORKER}: writable pipe handle={e.Handle} access={e.Access:#x}', flush=True)
                handles.append(dup)
            else:
                k.CloseHandle(dup)
    assert len(handles) == 1, f'Expected sole engine stdin writer, found {len(handles)}; no writes performed'
    engine = k.OpenProcess(0x100000 | 0x1000, False, ENGINE)
    assert engine, c.get_last_error()
    payload = b'stop\nquit\n'
    written = w.DWORD()
    assert k.WriteFile(handles[0], payload, len(payload), c.byref(written), None), c.get_last_error()
    assert written.value == len(payload)
    print(f'Sent UCI stop/quit ({written.value} bytes) to lc0 PID {ENGINE}; no forced engine termination', flush=True)
    assert k.WaitForSingleObject(engine, 30000) == 0, 'lc0 did not exit within 30 seconds'
    code = w.DWORD()
    assert k.GetExitCodeProcess(engine, c.byref(code))
    print(f'lc0 PID {ENGINE} exited cleanly, exit code={code.value}', flush=True)
    assert code.value == 0
    k.CloseHandle(engine)
finally:
    for handle in handles:
        k.CloseHandle(handle)
    k.CloseHandle(owner)
