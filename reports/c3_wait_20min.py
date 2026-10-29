"""Wait on the background controller; inspect state only every 20 min or exit."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import time

root = Path(__file__).resolve().parents[1]
pid = 12856
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k.OpenProcess.restype = wintypes.HANDLE
k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
k.CloseHandle.argtypes = [wintypes.HANDLE]
handle = k.OpenProcess(0x100000 | 0x1000, False, pid)
assert handle, ctypes.get_last_error()
try:
    while True:
        result = k.WaitForSingleObject(handle, 20 * 60 * 1000)
        assert result in (0, 258), result
        state = json.loads((root / 'reports/c3-part1/state.json').read_text(encoding='utf-8'))
        print(time.strftime('%Y-%m-%d %H:%M:%S %z'), json.dumps(state), flush=True)
        path = Path(state['log']) if state.get('log') else None
        if path and path.exists():
            print('\n'.join(path.read_bytes().decode('utf-8', errors='replace').splitlines()[-5:]), flush=True)
        if result == 0:
            code = wintypes.DWORD()
            assert k.GetExitCodeProcess(handle, ctypes.byref(code))
            print(f'CONTROLLER EXIT={code.value}; final status={state["status"]}', flush=True)
            break
finally:
    k.CloseHandle(handle)
