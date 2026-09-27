# Procedural Audio

The engine generates real audio waveform data from mathematical formulas — no sound files, no external libraries. Whether that data reaches your speakers as actual sound depends on one optional third-party package. This document explains both halves honestly, since the gap between them is easy to miss.

## Waveform Generation (real)

`Sound` computes genuine PCM sample arrays at a 22,050 Hz sample rate:

```python
from engine.audio.sound_generator import Sound

laser = Sound('laser')
laser.generate_sweep(800, 200, 0.1, 'square', 0.3)  # start, end, duration, wave, amplitude
print(len(laser.samples))  # 2205 real floating-point samples
```

Four generators are available:

- `generate_tone(frequency, duration, wave_type, amplitude)` — a fixed-frequency tone. `wave_type` is `'sine'`, `'square'`, `'sawtooth'`, `'triangle'`, or `'noise'`.
- `generate_sweep(start_freq, end_freq, duration, wave_type, amplitude)` — a frequency ramp with a short attack/release envelope. Good for laser-style effects. Only `'sine'`, `'square'`, `'sawtooth'`, and `'triangle'` are meaningful here; anything else falls back to sine.
- `generate_explosion(duration, amplitude)` — filtered noise with a decaying low-frequency tone mixed in and an exponential-decay envelope.
- `generate_engine(base_freq, duration, amplitude)` — a base tone plus two harmonics and light noise, for a sustained thrust/hum sound.

Each generator also records how the sound was made — `wave_type`, `base_frequency` or `start_freq`/`end_freq`, and `is_noise`/`is_continuous` flags — so `average_frequency()` can estimate a representative pitch later without re-deriving it from raw samples:

```python
laser.average_frequency()  # (800 + 200) / 2 == 500.0
```

## Playback: two paths, chosen automatically

There is no cross-platform way to send arbitrary PCM samples to an audio output device using only the Python standard library — no stdlib module opens a sound card on Windows, macOS, and Linux alike. `winsound` exists but is Windows-only; `ossaudiodev` could do it on Linux but was removed from the standard library in Python 3.13; nothing has ever existed for macOS. Reaching real speakers on all three platforms genuinely requires code outside the standard library — there's no clever workaround for that, only the choice of whether to accept the dependency.

So the engine offers both, and picks automatically:

- **With the optional `audio` extra installed** (`pip install pure-python-game-engine[audio]`, which pulls in [`miniaudio`](https://github.com/irmen/pyminiaudio)), `SoundGenerator` opens a real playback device and sends each sound's actual waveform samples to it. Distinct sounds genuinely sound distinct — a laser sweep sounds like a laser sweep, an explosion sounds like noise, an engine hum sounds like a hum. Multiple overlapping sounds (rapid-fire bullets, an explosion during an engine hum) are mixed together in real time rather than cutting each other off.
- **Without it**, or on a machine with no usable audio hardware at all (routine in CI and headless environments — `miniaudio` itself may be installed and still fail to find a device), `SoundGenerator` falls back to the terminal-bell approximation described below. Nothing breaks either way; `play_sound()` has the identical signature and behavior from the caller's perspective in both cases.

Check which path is active with `sound_generator.real_audio_enabled` (`True`/`False`). Run `python -m examples.games.asteroids_game` with the extra installed to hear the difference directly — its engine hum, bullet laser, and explosion sounds all use the built-in trio described below.

The real device is never garbage-collected on its own — it holds a native reference to itself so `miniaudio`'s C callback can look it up — so an `atexit` hook closes it automatically when your process exits, and every existing game keeps working with zero code changes. Call `SoundGenerator.shutdown()` yourself only if you want the device released earlier and deterministically (for example, between levels), not to avoid a hang.

### Why an optional dependency, not a required one

Making real audio a *hard* dependency would contradict the engine's core promise — zero required dependencies beyond the standard library, so `pip install pure-python-game-engine` always works standalone. Making it an *optional* one keeps that promise fully intact for anyone who doesn't need real sound, while still letting anyone who does get it with one extra pip argument, instead of being stuck with the terminal bell forever. [`miniaudio`](https://pypi.org/project/miniaudio/) was chosen specifically because it's self-contained on all three target platforms — unlike some alternatives (e.g. `sounddevice`, which wraps PortAudio), it doesn't additionally require a separate system library to already be installed on Linux.

### The terminal-bell fallback

When no real backend is available, `SoundGenerator.play_sound()` triggers the terminal bell (`\a`) in a background thread instead, with a rhythm chosen from the sound's generation metadata:

```python
sound = self.sounds[sound_name]
if sound.is_noise:
    # explosion-style: three quick beeps
elif sound.is_continuous:
    # engine/hum: one sustained beep
elif sound.average_frequency() >= 400:
    # bright/high-pitched: one immediate beep
else:
    # duller/low-pitched: one beep after a short delay
```

The terminal bell has no controllable pitch — every beep sounds identical regardless of which branch fires. The only real differentiation available is *when* and *how many times* it fires, not *how it sounds*. Two sounds with very different frequencies (say, a player's 800 Hz laser and an enemy's 250 Hz one) still produce the physically identical beep; they just fire on a different rhythm.

Any registered sound gets *some* playback pattern now — there's no per-name whitelist, so a sound you register yourself works the same way the four built-in ones do.

## Built-in Sounds

```python
from engine import SoundGenerator

sound_gen = SoundGenerator()
sound_gen.initialize_default_sounds()  # registers "bullet", "explosion", "engine"
sound_gen.play_sound("bullet")
```

`create_bullet_sound()`, `create_explosion_sound()`, and `create_engine_sound()` are thin wrappers that build a `Sound`, call the matching generator with tuned parameters, and return it — register a custom `Sound` the same way to add your own.

## Current Scope

- Real audio output requires the optional `audio` extra (`pip install pure-python-game-engine[audio]`); without it, or without a usable audio device, playback differentiation is limited to timing/rhythm — pitch, timbre, and volume are not reproduced.
- The real-audio mixer sums overlapping sounds and clips at full scale rather than doing any loudness normalization — many sounds firing at once can sound harsh rather than automatically balanced.
- `generate_sweep()`'s `'noise'` wave type isn't implemented (only `generate_tone()` supports it) — passing it to `generate_sweep()` silently falls back to sine.
- `SoundGenerator.generate_frequency_beep()` exists but is unused by any game or demo in this repository.
