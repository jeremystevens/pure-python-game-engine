# Procedural Audio

The engine generates real audio waveform data from mathematical formulas — no sound files, no external libraries. What it does *not* do is play that data as actual sound. This document explains both halves honestly, since the gap between them is easy to miss.

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

## Playback (approximated, not real audio)

There is no cross-platform way to send arbitrary PCM samples to an audio output device using only the Python standard library — no stdlib module opens a sound card on Windows, macOS, and Linux alike. `winsound` exists but is Windows-only; everything else would mean shelling out to a platform-specific player binary, which this engine deliberately avoids to stay dependency-free.

So `SoundGenerator.play_sound()` doesn't play the samples at all. It triggers the terminal bell (`\a`) instead, in a background thread, with a rhythm chosen from the sound's generation metadata:

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

- No real audio output. If you need actual sound, this engine cannot provide it without stepping outside the standard library.
- Playback differentiation is limited to timing/rhythm; pitch, timbre, and volume are not reproduced.
- `generate_sweep()`'s `'noise'` wave type isn't implemented (only `generate_tone()` supports it) — passing it to `generate_sweep()` silently falls back to sine.
- `SoundGenerator.generate_frequency_beep()` exists but is unused by any game or demo in this repository.
