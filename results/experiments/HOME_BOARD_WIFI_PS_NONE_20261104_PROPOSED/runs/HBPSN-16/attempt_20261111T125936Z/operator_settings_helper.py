"""HBPSN-16 operator-run settings helper. Standard library only.

Run it in the operator's own PowerShell window with the same Python as the collector.
It never opens COM6, never touches Clumsy and never starts the collector.

  --test-dir DIR   one screen capture into DIR, then exit; no run folder is read
  --run-dir DIR    wait for pre_run then end_of_run requests and answer each one

The full screen is captured only after a request appears. The observed settings come
from clumsy_declaration.json, which the operator confirms before launch. Nothing in
the request's "expected" block is used.
"""
import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
import struct
import sys
import time
import zlib
from ctypes import wintypes
from pathlib import Path

PROVENANCE = ('capture_*_utc and capture_*_monotonic sampled directly in this helper around the screen copy, '
              'using datetime.now(UTC) and time.monotonic() under the same Python as the collector.')
LABELS = {
    'pre_run': ('HBPSN-16 TCP_TLS LAG100_OUT operator-run full-screen capture taken after the nonce request. Observed values come '
                'from the operator declaration confirmed before launch; they were not machine-read from this image.'),
    'end_of_run': ('HBPSN-16 TCP_TLS LAG100_OUT operator-run full-screen capture taken after the end-of-run request. Observed values '
                   'come from the declaration confirmed BEFORE launch and were not re-inspected at this moment; this image and '
                   'operator stability need manual review.'),
}


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
                ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
                ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]


def utc_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def grab_screen():
    """Return (width, height, BGRA bytes) for the whole virtual desktop."""
    try:
        ctypes.WinDLL('shcore').SetProcessDpiAwareness(2)
    except OSError:
        pass
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
    gdi32.BitBlt.restype = wintypes.BOOL
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                                ctypes.POINTER(BITMAPINFOHEADER), wintypes.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    x, y = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
    width, height = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
    if width <= 0 or height <= 0:
        raise RuntimeError(f'Invalid screen size {width}x{height}')
    screen = user32.GetDC(None)
    if not screen:
        raise ctypes.WinError(ctypes.get_last_error())
    memory = bitmap = old = None
    try:
        memory = gdi32.CreateCompatibleDC(screen)
        bitmap = gdi32.CreateCompatibleBitmap(screen, width, height)
        if not memory or not bitmap:
            raise ctypes.WinError(ctypes.get_last_error())
        old = gdi32.SelectObject(memory, bitmap)
        if not gdi32.BitBlt(memory, 0, 0, width, height, screen, x, y, 0x00CC0020 | 0x40000000):
            raise ctypes.WinError(ctypes.get_last_error())
        header = BITMAPINFOHEADER(biSize=ctypes.sizeof(BITMAPINFOHEADER), biWidth=width, biHeight=-height, biPlanes=1, biBitCount=32, biCompression=0)
        buffer = ctypes.create_string_buffer(width * height * 4)
        if gdi32.GetDIBits(memory, bitmap, 0, height, buffer, ctypes.byref(header), 0) != height:
            raise ctypes.WinError(ctypes.get_last_error())
        return width, height, buffer.raw
    finally:
        if old:
            gdi32.SelectObject(memory, old)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if memory:
            gdi32.DeleteDC(memory)
        user32.ReleaseDC(None, screen)


def encode_png(width, height, bgra):
    if len({bgra[i:i + 3] for i in range(0, len(bgra), 4 * 997)}) < 2:
        raise RuntimeError('Screen capture is one solid colour; the desktop may be locked or disconnected.')
    rgb = bytearray(width * height * 3)
    rgb[0::3], rgb[1::3], rgb[2::3] = bgra[2::4], bgra[1::4], bgra[0::4]
    stride = width * 3
    raw = b''.join(b'\0' + bytes(rgb[row * stride:(row + 1) * stride]) for row in range(height))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def load_observed(run_dir):
    value = json.loads((run_dir / 'clumsy_declaration.json').read_text(encoding='utf-8'))
    if value.get('operator_confirmed') is not True:
        raise SystemExit('REFUSED: clumsy_declaration.json has operator_confirmed false. No response will be written.')
    if value.get('run_id') != 'HBPSN-16' or value.get('attempt_id') != run_dir.name:
        raise SystemExit('REFUSED: clumsy_declaration.json does not name this run and attempt.')
    return value['observed']


def service(run_dir, phase, observed, not_before, timeout, grab=grab_screen):
    """Wait for one request created after not_before, capture, then answer it."""
    folder = run_dir / 'settings_requests'
    request_path, response_path = folder / f'{phase}.request.json', folder / f'{phase}.response.json'
    until = time.monotonic() + timeout
    print(f'[{utc_iso()}] Waiting for {phase} request', flush=True)
    while True:
        try:
            request = json.loads(request_path.read_text(encoding='utf-8'))
            if dt.datetime.fromisoformat(request['requested_utc']) >= not_before:
                break
        except (FileNotFoundError, PermissionError, json.JSONDecodeError, KeyError):
            pass
        if time.monotonic() > until:
            print(f'[{utc_iso()}] No {phase} request within {timeout} s. No response written.', flush=True)
            return False
        time.sleep(0.02)
    if request.get('phase') != phase:
        raise RuntimeError('Request phase mismatch')
    image = run_dir / f'clumsy_operator_{phase}.png'
    started_utc, started_mono = utc_iso(), time.monotonic()
    width, height, pixels = grab()
    completed_utc, completed_mono = utc_iso(), time.monotonic()
    data = encode_png(width, height, pixels)
    with image.open('xb') as f:
        f.write(data)
    response = dict(nonce=request['nonce'], screenshot=image.name, sha256=hashlib.sha256(data).hexdigest(),
                    capture_started_utc=started_utc, capture_completed_utc=completed_utc,
                    capture_started_monotonic=started_mono, capture_completed_monotonic=completed_mono,
                    clock_provenance=PROVENANCE, source_type='operator_reported', observed=observed, label=LABELS[phase])
    temporary = response_path.with_name(response_path.name + '.tmp')
    temporary.write_text(json.dumps(response, indent=2), encoding='utf-8')
    os.replace(temporary, response_path)
    print(f'[{utc_iso()}] Answered {phase}: {image.name} {width}x{height} {response["sha256"]}', flush=True)
    return True


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test-dir', type=Path)
    mode.add_argument('--run-dir', type=Path)
    args = parser.parse_args()
    if args.test_dir:
        args.test_dir.mkdir(parents=True, exist_ok=False)
        width, height, pixels = grab_screen()
        path = args.test_dir / 'test_capture.png'
        path.write_bytes(encode_png(width, height, pixels))
        print(f'TEST CAPTURE OK: {path} {width}x{height} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}')
        return
    run_dir = args.run_dir.resolve()
    observed = load_observed(run_dir)
    started = dt.datetime.now(dt.timezone.utc)
    print('Helper armed. Keep Clumsy fully visible and this window open until it says finished.', flush=True)
    if not service(run_dir, 'pre_run', observed, started, 900):
        sys.exit(1)
    answered = service(run_dir, 'end_of_run', observed, started, 3600)
    print(f'[{utc_iso()}] Helper finished. end_of_run answered: {answered}', flush=True)


if __name__ == '__main__':
    main()
