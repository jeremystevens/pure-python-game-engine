"""Optional real audio output via the third-party ``miniaudio`` package.

The engine core has zero required dependencies. This module is only ever
imported by :mod:`engine.audio.sound_generator`, and its ``RealAudioBackend``
is only ever *used* when ``miniaudio`` is both installed and able to open a
real playback device. There is no way to open an audio output device on
Windows, macOS, and Linux alike using the standard library alone -- see
``docs/AUDIO.md`` for exactly why -- so this capability is opt-in:

    pip install pure-python-game-engine[audio]

Without it, or on a machine with no usable audio hardware (common in CI and
headless environments), ``SoundGenerator`` falls back to its terminal-bell
approximation exactly as it did before this module existed.
"""

import array
import atexit
import threading
from typing import Dict, List, Sequence

try:
    import miniaudio
except ImportError:  # pragma: no cover - exercised by environments without the extra
    miniaudio = None


class Mixer:
    """Sums any number of overlapping sample lists into fixed-size frames.

    Deliberately pure Python and independent of ``miniaudio``, so its mixing
    behavior can be unit tested regardless of whether the optional
    dependency -- or a real audio device -- is available in the current
    environment.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._voices: List[Dict] = []

    def play(self, samples: Sequence[float]):
        """Start mixing in a sound's samples from the beginning."""
        if not samples:
            return
        with self._lock:
            self._voices.append({'samples': samples, 'position': 0})

    def render(self, frame_count: int) -> array.array:
        """Return exactly ``frame_count`` mixed, clipped float32 samples."""
        mixed = array.array('f', [0.0]) * frame_count
        with self._lock:
            still_active = []
            for voice in self._voices:
                samples = voice['samples']
                position = voice['position']
                take = min(frame_count, len(samples) - position)
                for i in range(take):
                    mixed[i] += samples[position + i]
                position += take
                voice['position'] = position
                if position < len(samples):
                    still_active.append(voice)
            self._voices = still_active

        for i, value in enumerate(mixed):
            if value > 1.0:
                mixed[i] = 1.0
            elif value < -1.0:
                mixed[i] = -1.0
        return mixed

    @property
    def active_voice_count(self) -> int:
        """Return how many sounds are currently mixed into playback."""
        with self._lock:
            return len(self._voices)


class RealAudioBackend:
    """Owns a real playback device and feeds it continuously mixed audio.

    Raises whatever ``miniaudio`` raises (or ``RuntimeError`` if the package
    itself isn't installed) if a device can't be opened -- callers are
    expected to catch that and fall back gracefully rather than treat it as
    fatal, since "no usable audio backend" is routine on headless machines.
    """

    def __init__(self, sample_rate: int):
        if miniaudio is None:
            raise RuntimeError("miniaudio is not installed")

        self.mixer = Mixer()
        generator = self._stream()
        next(generator)  # prime it, per miniaudio's generator protocol

        self._device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.FLOAT32,
            nchannels=1,
            sample_rate=sample_rate,
            buffersize_msec=50,
        )
        self._device.start(generator)

        # The open device holds a native reference to itself (miniaudio's
        # C callback needs to look the Python object back up), so it is
        # never garbage-collected on its own -- without this, a process
        # that never calls SoundGenerator.shutdown() explicitly hangs
        # forever after the game window closes, instead of exiting. This
        # is what lets every existing game keep working with zero code
        # changes once the optional extra is installed.
        atexit.register(self.close)

    def play(self, samples: Sequence[float]):
        """Mix a sound's samples into the ongoing playback."""
        self.mixer.play(samples)

    def close(self):
        """Stop and release the playback device."""
        self._device.close()

    def _stream(self):
        frame_count = yield array.array('f', [])
        while True:
            frame_count = yield self.mixer.render(frame_count)
