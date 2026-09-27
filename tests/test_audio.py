import unittest

from engine.audio.sound_generator import Sound, SoundGenerator


class SoundGenerationTests(unittest.TestCase):
    def test_generate_tone_records_duration_samples_and_metadata(self):
        sound = Sound('tone')
        sound.generate_tone(440, 0.1, 'square', 0.5)

        self.assertEqual(sound.duration, 0.1)
        self.assertEqual(len(sound.samples), int(sound.sample_rate * 0.1))
        self.assertEqual(sound.wave_type, 'square')
        self.assertEqual(sound.base_frequency, 440)
        self.assertEqual(sound.average_frequency(), 440)
        self.assertFalse(sound.is_noise)
        self.assertFalse(sound.is_continuous)

    def test_generate_sweep_records_frequency_range_and_averages_it(self):
        sound = Sound('sweep')
        sound.generate_sweep(800, 200, 0.05, 'square', 0.3)

        self.assertEqual(sound.start_freq, 800)
        self.assertEqual(sound.end_freq, 200)
        self.assertEqual(sound.average_frequency(), 500.0)
        self.assertEqual(len(sound.samples), int(sound.sample_rate * 0.05))

    def test_generate_explosion_marks_sound_as_noise(self):
        sound = Sound('explosion')
        sound.generate_explosion(0.05, 0.4)

        self.assertTrue(sound.is_noise)
        self.assertFalse(sound.is_continuous)
        self.assertEqual(sound.average_frequency(), 0.0)
        self.assertEqual(len(sound.samples), int(sound.sample_rate * 0.05))

    def test_generate_engine_marks_sound_as_continuous(self):
        sound = Sound('engine')
        sound.generate_engine(100, 0.05, 0.25)

        self.assertTrue(sound.is_continuous)
        self.assertFalse(sound.is_noise)
        self.assertEqual(sound.average_frequency(), 100)

    def test_average_frequency_defaults_to_zero_before_generation(self):
        self.assertEqual(Sound('empty').average_frequency(), 0.0)

    def test_all_tone_wave_types_produce_samples_without_error(self):
        for wave_type in ('sine', 'square', 'sawtooth', 'triangle', 'noise', 'unknown'):
            sound = Sound(wave_type)
            sound.generate_tone(300, 0.02, wave_type, 0.5)
            self.assertEqual(len(sound.samples), int(sound.sample_rate * 0.02))


class SoundGeneratorTests(unittest.TestCase):
    def join_playback_thread(self, generator, timeout=1.0):
        # play_sound() fires a daemon thread; join it so it can't still be
        # sleeping (explosions sleep up to 0.15s) when the process exits,
        # which otherwise races interpreter shutdown and prints a scary but
        # harmless "Fatal Python error" from the standard library.
        if generator.current_thread is not None:
            generator.current_thread.join(timeout)

    def test_register_and_play_known_sound_does_not_raise(self):
        generator = SoundGenerator()
        sound = Sound('beep')
        sound.generate_tone(500, 0.01, 'sine', 0.2)
        generator.register_sound(sound)

        generator.play_sound('beep')  # should not raise
        self.join_playback_thread(generator)

        self.assertIn('beep', generator.sounds)

    def test_playing_an_unregistered_sound_is_a_silent_no_op(self):
        generator = SoundGenerator()
        generator.play_sound('does-not-exist')  # should not raise
        self.assertIsNone(generator.current_thread)

    def test_initialize_default_sounds_registers_bullet_explosion_engine(self):
        generator = SoundGenerator()
        generator.initialize_default_sounds()

        self.assertEqual(set(generator.sounds), {'bullet', 'explosion', 'engine'})
        self.assertTrue(generator.sounds['explosion'].is_noise)
        self.assertTrue(generator.sounds['engine'].is_continuous)
        self.assertGreaterEqual(generator.sounds['bullet'].average_frequency(), 200)

    def test_create_bullet_explosion_and_engine_sounds_are_independently_playable(self):
        generator = SoundGenerator()
        for sound in (
            generator.create_bullet_sound(),
            generator.create_explosion_sound(),
            generator.create_engine_sound(),
        ):
            generator.register_sound(sound)
            generator.play_sound(sound.name)  # should not raise for any of them
            self.join_playback_thread(generator)


if __name__ == '__main__':
    unittest.main()
