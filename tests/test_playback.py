import array
import unittest
from unittest import mock

from engine.audio.playback import Mixer, RealAudioBackend
from engine.audio.sound_generator import Sound, SoundGenerator


class MixerTests(unittest.TestCase):
    def test_render_before_any_sound_is_silence(self):
        mixer = Mixer()
        self.assertEqual(list(mixer.render(4)), [0.0, 0.0, 0.0, 0.0])

    def test_play_then_render_returns_the_samples(self):
        mixer = Mixer()
        mixer.play([0.1, 0.2, 0.3])
        rendered = list(mixer.render(3))
        for actual, expected in zip(rendered, [0.1, 0.2, 0.3]):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_render_pads_with_silence_past_a_finished_voice(self):
        mixer = Mixer()
        mixer.play([0.5, 0.5])
        self.assertEqual(list(mixer.render(4)), [0.5, 0.5, 0.0, 0.0])

    def test_finished_voice_is_dropped_and_stays_silent(self):
        mixer = Mixer()
        mixer.play([0.5])
        mixer.render(1)
        self.assertEqual(mixer.active_voice_count, 0)
        self.assertEqual(list(mixer.render(2)), [0.0, 0.0])

    def test_overlapping_voices_sum_together(self):
        mixer = Mixer()
        mixer.play([0.2, 0.2, 0.2])
        mixer.play([0.3, 0.3])
        rendered = list(mixer.render(3))
        self.assertAlmostEqual(rendered[0], 0.5, places=5)
        self.assertAlmostEqual(rendered[1], 0.5, places=5)
        self.assertAlmostEqual(rendered[2], 0.2, places=5)

    def test_overlapping_voices_clip_instead_of_overflowing(self):
        mixer = Mixer()
        mixer.play([0.8, -0.8])
        mixer.play([0.8, -0.8])
        rendered = list(mixer.render(2))
        self.assertEqual(rendered[0], 1.0)
        self.assertEqual(rendered[1], -1.0)

    def test_playing_empty_samples_is_a_no_op(self):
        mixer = Mixer()
        mixer.play([])
        self.assertEqual(mixer.active_voice_count, 0)

    def test_render_returns_an_array_of_floats(self):
        mixer = Mixer()
        rendered = mixer.render(2)
        self.assertIsInstance(rendered, array.array)
        self.assertEqual(rendered.typecode, 'f')


class RealAudioBackendTests(unittest.TestCase):
    """Exercise the miniaudio wiring with a fake module -- no real device
    or the optional dependency itself needs to be present to run these."""

    def _fake_miniaudio(self):
        fake = mock.MagicMock()
        fake.SampleFormat.FLOAT32 = 'FLOAT32'
        device_instances = []

        def make_device(**kwargs):
            device = mock.MagicMock()
            device.init_kwargs = kwargs
            device_instances.append(device)
            return device

        fake.PlaybackDevice.side_effect = make_device
        return fake, device_instances

    def test_backend_opens_a_device_and_starts_a_primed_generator(self):
        fake_miniaudio, devices = self._fake_miniaudio()
        with mock.patch('engine.audio.playback.miniaudio', fake_miniaudio):
            backend = RealAudioBackend(sample_rate=22050)

        self.assertEqual(len(devices), 1)
        device = devices[0]
        self.assertEqual(device.init_kwargs['sample_rate'], 22050)
        self.assertEqual(device.init_kwargs['nchannels'], 1)
        device.start.assert_called_once()

        # The generator handed to start() must already be primed (past its
        # first yield), per miniaudio's documented generator protocol.
        generator = device.start.call_args.args[0]
        frame = generator.send(4)
        self.assertEqual(len(frame), 4)

        backend.close()
        device.close.assert_called_once()

    def test_backend_raises_when_miniaudio_is_not_installed(self):
        with mock.patch('engine.audio.playback.miniaudio', None):
            with self.assertRaises(RuntimeError):
                RealAudioBackend(sample_rate=22050)

    def test_play_forwards_samples_into_the_mixer(self):
        fake_miniaudio, _ = self._fake_miniaudio()
        with mock.patch('engine.audio.playback.miniaudio', fake_miniaudio):
            backend = RealAudioBackend(sample_rate=22050)

        backend.play([0.1, 0.2])
        self.assertEqual(backend.mixer.active_voice_count, 1)


class SoundGeneratorBackendWiringTests(unittest.TestCase):
    """SoundGenerator must degrade gracefully whenever a real backend can't
    be built, and must use one transparently whenever it can."""

    def test_falls_back_to_beep_thread_when_backend_cannot_be_built(self):
        with mock.patch(
            'engine.audio.sound_generator.RealAudioBackend',
            side_effect=RuntimeError("no audio device"),
        ):
            generator = SoundGenerator()

        self.assertFalse(generator.real_audio_enabled)

        sound = Sound('beep')
        sound.generate_tone(500, 0.01, 'sine', 0.2)
        generator.register_sound(sound)
        generator.play_sound('beep')
        if generator.current_thread is not None:
            generator.current_thread.join(1.0)

    def test_uses_real_backend_when_available_instead_of_beeping(self):
        fake_backend = mock.MagicMock()
        with mock.patch(
            'engine.audio.sound_generator.RealAudioBackend',
            return_value=fake_backend,
        ):
            generator = SoundGenerator()

        self.assertTrue(generator.real_audio_enabled)

        sound = Sound('beep')
        sound.generate_tone(500, 0.01, 'sine', 0.2)
        generator.register_sound(sound)
        generator.play_sound('beep')

        fake_backend.play.assert_called_once_with(sound.samples)
        self.assertIsNone(generator.current_thread)  # no beep thread spawned

    def test_shutdown_closes_and_clears_the_backend(self):
        fake_backend = mock.MagicMock()
        with mock.patch(
            'engine.audio.sound_generator.RealAudioBackend',
            return_value=fake_backend,
        ):
            generator = SoundGenerator()

        generator.shutdown()
        fake_backend.close.assert_called_once()
        self.assertFalse(generator.real_audio_enabled)

        generator.shutdown()  # calling twice must not raise


if __name__ == '__main__':
    unittest.main()
