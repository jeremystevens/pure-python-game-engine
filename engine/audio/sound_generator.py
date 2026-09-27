
"""
Procedural sound generation system
Creates audio effects using mathematical waveforms without requiring audio files
"""
import math
import threading
import time
from typing import List, Optional
import tkinter as tk

from .playback import RealAudioBackend


class Sound:
    """Represents a procedurally generated sound effect"""
    
    def __init__(self, name: str):
        self.name = name
        self.samples: List[float] = []
        self.sample_rate = 22050
        self.duration = 0.0

        # Generation metadata, used by SoundGenerator to pick a playback pattern
        self.wave_type: Optional[str] = None
        self.base_frequency: Optional[float] = None
        self.start_freq: Optional[float] = None
        self.end_freq: Optional[float] = None
        self.is_noise = False
        self.is_continuous = False

    def average_frequency(self) -> float:
        """Estimate a representative frequency for this sound based on how it was generated"""
        if self.start_freq is not None and self.end_freq is not None:
            return (self.start_freq + self.end_freq) / 2
        if self.base_frequency is not None:
            return self.base_frequency
        return 0.0

    def generate_tone(self, frequency: float, duration: float, wave_type: str = 'sine', amplitude: float = 0.5):
        """Generate a basic tone"""
        self.duration = duration
        self.wave_type = wave_type
        self.base_frequency = frequency
        num_samples = int(self.sample_rate * duration)
        self.samples = []
        
        for i in range(num_samples):
            t = i / self.sample_rate
            
            if wave_type == 'sine':
                sample = amplitude * math.sin(2 * math.pi * frequency * t)
            elif wave_type == 'square':
                sample = amplitude * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1)
            elif wave_type == 'sawtooth':
                sample = amplitude * (2 * (t * frequency - math.floor(t * frequency + 0.5)))
            elif wave_type == 'triangle':
                sample = amplitude * (2 * abs(2 * (t * frequency - math.floor(t * frequency + 0.5))) - 1)
            elif wave_type == 'noise':
                import random
                sample = amplitude * (random.random() * 2 - 1)
            else:
                sample = 0
                
            self.samples.append(sample)
    
    def generate_sweep(self, start_freq: float, end_freq: float, duration: float, wave_type: str = 'sine', amplitude: float = 0.5):
        """Generate a frequency sweep (good for laser sounds)"""
        self.duration = duration
        self.wave_type = wave_type
        self.start_freq = start_freq
        self.end_freq = end_freq
        num_samples = int(self.sample_rate * duration)
        self.samples = []
        
        for i in range(num_samples):
            t = i / self.sample_rate
            progress = t / duration
            frequency = start_freq + (end_freq - start_freq) * progress
            
            if wave_type == 'sine':
                sample = amplitude * math.sin(2 * math.pi * frequency * t)
            elif wave_type == 'square':
                sample = amplitude * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1)
            elif wave_type == 'sawtooth':
                sample = amplitude * (2 * (t * frequency - math.floor(t * frequency + 0.5)))
            elif wave_type == 'triangle':
                sample = amplitude * (2 * abs(2 * (t * frequency - math.floor(t * frequency + 0.5))) - 1)
            else:
                sample = amplitude * math.sin(2 * math.pi * frequency * t)
                
            # Apply envelope for smoother sound
            envelope = 1.0
            if t < 0.01:  # Attack
                envelope = t / 0.01
            elif t > duration - 0.05:  # Release
                envelope = (duration - t) / 0.05
                
            self.samples.append(sample * envelope)
    
    def generate_explosion(self, duration: float = 0.5, amplitude: float = 0.3):
        """Generate explosion sound using filtered noise"""
        self.duration = duration
        self.is_noise = True
        num_samples = int(self.sample_rate * duration)
        self.samples = []
        
        import random
        
        for i in range(num_samples):
            t = i / self.sample_rate
            progress = t / duration
            
            # Start with noise
            sample = random.random() * 2 - 1
            
            # Apply low-pass filter effect by mixing with lower frequencies
            low_freq = 100 * (1 - progress)  # Frequency decreases over time
            low_tone = math.sin(2 * math.pi * low_freq * t)
            sample = sample * 0.7 + low_tone * 0.3
            
            # Apply envelope (sharp attack, long decay)
            envelope = math.exp(-progress * 5)  # Exponential decay
            
            self.samples.append(sample * amplitude * envelope)
    
    def generate_engine(self, base_freq: float = 80, duration: float = 0.2, amplitude: float = 0.2):
        """Generate engine/thrust sound"""
        self.duration = duration
        self.is_continuous = True
        self.base_frequency = base_freq
        num_samples = int(self.sample_rate * duration)
        self.samples = []
        
        import random
        
        for i in range(num_samples):
            t = i / self.sample_rate
            
            # Base engine tone
            engine_tone = math.sin(2 * math.pi * base_freq * t)
            
            # Add harmonics for richness
            harmonic1 = 0.3 * math.sin(2 * math.pi * base_freq * 2 * t)
            harmonic2 = 0.1 * math.sin(2 * math.pi * base_freq * 3 * t)
            
            # Add some noise for realism
            noise = (random.random() * 2 - 1) * 0.1
            
            # Combine all components
            sample = engine_tone + harmonic1 + harmonic2 + noise
            
            # Apply envelope
            envelope = 1.0
            if t < 0.05:  # Quick attack
                envelope = t / 0.05
            elif t > duration - 0.1:  # Quick release
                envelope = (duration - t) / 0.1
                
            self.samples.append(sample * amplitude * envelope)


class SoundGenerator:
    """Manages procedural sound generation and playback"""
    
    def __init__(self):
        self.sounds = {}
        self.playing = False
        self.current_thread = None

        # Try to use system beep as fallback
        self.has_audio = True

        # Optional real playback backend (see docs/AUDIO.md). None whenever
        # it can't be built -- miniaudio isn't installed, or no usable audio
        # device exists (routine on headless machines) -- in which case
        # play_sound() falls back to the terminal-bell approximation below.
        self._backend: Optional[RealAudioBackend] = None
        try:
            self._backend = RealAudioBackend(sample_rate=22050)
        except Exception:
            self._backend = None

    @property
    def real_audio_enabled(self) -> bool:
        """Whether sounds are actually reaching a real audio device."""
        return self._backend is not None

    def shutdown(self):
        """Release the real audio device now, if one was opened.

        Safe to call even when no real backend exists. An atexit hook
        already closes the device automatically when your process exits
        (it holds a native self-reference and is never garbage-collected
        on its own), so calling this yourself is only useful for earlier,
        deterministic teardown -- for example, between levels.
        """
        if self._backend is not None:
            self._backend.close()
            self._backend = None

    def create_bullet_sound(self) -> Sound:
        """Create a laser bullet sound effect"""
        sound = Sound("bullet")
        # High frequency sweep down - classic laser sound
        sound.generate_sweep(800, 200, 0.1, 'square', 0.3)
        return sound
    
    def create_explosion_sound(self) -> Sound:
        """Create an explosion sound effect"""
        sound = Sound("explosion") 
        sound.generate_explosion(0.3, 0.4)
        return sound
    
    def create_engine_sound(self) -> Sound:
        """Create a rocket engine sound effect"""
        sound = Sound("engine")
        sound.generate_engine(100, 0.15, 0.25)
        return sound
    
    def register_sound(self, sound: Sound):
        """Register a sound for later playback"""
        self.sounds[sound.name] = sound
    
    def play_sound(self, sound_name: str):
        """Play a registered sound through a real device, or approximate it.

        If the optional ``miniaudio`` dependency is installed and a real
        audio device is available, this sends the sound's actual waveform
        samples to it -- distinct sounds genuinely sound distinct. Otherwise
        it falls back to the terminal bell (`\\a`), which can't reproduce
        pitch at all: distinct sounds are approximated only by beep
        rhythm/count, derived from how the sound was generated (noise,
        continuous, or average frequency) rather than a fixed per-name
        whitelist. See ``docs/AUDIO.md`` for the full picture.
        """
        if sound_name not in self.sounds:
            return

        sound = self.sounds[sound_name]

        if self._backend is not None:
            self._backend.play(sound.samples)
            return

        try:
            def play_pattern():
                if sound.is_noise:
                    # Explosion-style: sharp burst of beeps
                    for _ in range(3):
                        print('\a', end='', flush=True)
                        time.sleep(0.05)
                elif sound.is_continuous:
                    # Engine/hum: single sustained beep
                    print('\a', end='', flush=True)
                else:
                    avg_freq = sound.average_frequency()
                    if avg_freq >= 400:
                        # Bright, high-pitched zap (e.g. a player laser)
                        print('\a', end='', flush=True)
                    else:
                        # Duller, lower-pitched shot (e.g. an enemy laser) -
                        # a short pre-delay gives it a heavier feel since the
                        # bell itself can't change pitch
                        time.sleep(0.03)
                        print('\a', end='', flush=True)

            # Play in separate thread to avoid blocking
            if self.current_thread is None or not self.current_thread.is_alive():
                self.current_thread = threading.Thread(target=play_pattern, daemon=True)
                self.current_thread.start()

        except (OSError, RuntimeError):
            # Fallback: just print sound effect
            print(f"*{sound_name}*", end=' ', flush=True)
    
    def generate_frequency_beep(self, frequency: float, duration: float):
        """Generate a simple frequency-based beep using print patterns"""
        # Different patterns for different frequency ranges
        if frequency > 500:
            pattern = "beep!"
        elif frequency > 200:
            pattern = "boop!"
        else:
            pattern = "boom!"
            
        print(pattern, end=' ', flush=True)
    
    def initialize_default_sounds(self):
        """Create and register default game sounds"""
        # Create bullet sound
        bullet_sound = self.create_bullet_sound()
        self.register_sound(bullet_sound)
        
        # Create explosion sound
        explosion_sound = self.create_explosion_sound()
        self.register_sound(explosion_sound)
        
        # Create engine sound
        engine_sound = self.create_engine_sound()
        self.register_sound(engine_sound)
        
        print("Procedural sound system initialized!")
        print("Available sounds: bullet, explosion, engine")
