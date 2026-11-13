"""CRC-checked, raw 12-bit Due acquisition. No digital filtering here."""
from collections import deque
import struct
import threading
import time
import zlib
import numpy as np

MAGIC = b'EMG1'
HEADER = struct.Struct('<4sBBHIIIIH')


def encode_packet(seq, tick, values, overruns=0, late=0):
    """Protocol reference encoder used in tests; not an acquisition substitute."""
    body = HEADER.pack(MAGIC, 1, 12, 2000, seq, tick, overruns, late, len(values))
    body += np.asarray(values, dtype='<u2').tobytes()
    return body + struct.pack('<I', zlib.crc32(body))


class Parser:
    def __init__(self):
        self.buffer = bytearray()
        self.corrupt = 0
        self.discarded = 0

    def feed(self, data):
        self.buffer.extend(data)
        packets = []
        while len(self.buffer) >= HEADER.size:
            pos = self.buffer.find(MAGIC)
            if pos < 0:
                self.discarded += len(self.buffer) - 3
                del self.buffer[:-3]
                break
            if pos:
                self.discarded += pos
                del self.buffer[:pos]
            if len(self.buffer) < HEADER.size:
                break
            _, version, bits, fs, seq, tick, overruns, late, n = HEADER.unpack_from(self.buffer)
            if version != 1 or bits != 12 or fs != 2000 or not 1 <= n <= 32:
                self.corrupt += 1
                del self.buffer[0]
                continue
            length = HEADER.size + n * 2 + 4
            if len(self.buffer) < length:
                break
            frame = bytes(self.buffer[:length])
            if zlib.crc32(frame[:-4]) != struct.unpack_from('<I', frame, length - 4)[0]:
                self.corrupt += 1
                del self.buffer[0]
                continue
            values = np.frombuffer(frame, '<u2', n, HEADER.size).copy()
            if np.any(values > 4095):
                self.corrupt += 1
            else:
                packets.append((seq, tick, overruns, late, values))
            del self.buffer[:length]
        return packets


class Reader:
    def __init__(self, port, baud=115200):
        self.port, self.baud = port, baud
        self.parser = Parser()
        self.samples = deque(maxlen=40000)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.error = ''
        self.received = self.missing = self.overruns = self.late = 0
        self.last_rx = 0.0
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        import serial
        try:
            with serial.Serial(self.port, self.baud, timeout=0.1, write_timeout=1) as link:
                self.link = link
                if self.stop_event.is_set():
                    return
                link.reset_input_buffer()
                link.write(b'S')
                expected, last_tick, epoch, offset = None, None, 0, None
                last_request = time.monotonic()
                while not self.stop_event.is_set():
                    chunk = link.read(min(max(link.in_waiting, 1), 8192))
                    rx = time.monotonic()
                    # Native USB can answer immediately; programming-port firmware
                    # can answer a retry once its reset/startup has completed.
                    if not self.received and rx - last_request > .5:
                        link.write(b'S')
                        last_request = rx
                    for seq, tick, overruns, late, values in self.parser.feed(chunk):
                        if expected is not None:
                            gap = (seq - expected) & 0xffffffff
                            if gap > 0x7fffffff:
                                raise RuntimeError('Device restarted/out-of-order data. Reconnect and start a new session.')
                            self.missing += gap
                        expected = (seq + len(values)) & 0xffffffff
                        if last_tick is not None and tick < last_tick:
                            epoch += 2**32
                        last_tick = tick
                        device = (epoch + tick) / 1e6
                        estimate = rx - (device + (len(values) - 1) / 2000)
                        offset = estimate if offset is None else min(offset, estimate)
                        # Host alignment is approximate: USB/camera latency is NOT measured away.
                        rows = [(device + offset + i / 2000, (seq + i) & 0xffffffff,
                                 device + i / 2000, int(v)) for i, v in enumerate(values)]
                        with self.lock:
                            self.samples.extend(rows)
                        self.received += len(values)
                        self.overruns, self.late, self.last_rx = overruns, late, rx
                link.write(b'X')
        except Exception as exc:
            self.error = str(exc)

    def snapshot(self, start=None, end=None):
        with self.lock:
            rows = list(self.samples)
        if start is not None:
            rows = [r for r in rows if r[0] >= start]
        if end is not None:
            rows = [r for r in rows if r[0] <= end]
        return np.asarray(rows, dtype=float).reshape(-1, 4)

    def diagnostics(self):
        return dict(samples=self.received, missing=self.missing, corrupt=self.parser.corrupt,
                    discarded_bytes=self.parser.discarded, overruns=self.overruns, late=self.late)

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=2)
