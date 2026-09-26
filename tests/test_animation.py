import unittest

from engine.assets import AnimationClip, SpriteAnimation


class AnimationClipTests(unittest.TestCase):
    def test_clip_copies_frames_and_is_immutable(self):
        frames = ['idle_0', 'idle_1']
        clip = AnimationClip.from_frames('idle', frames, 0.2, loop=True)
        frames.append('idle_2')

        self.assertEqual(clip.frames, ('idle_0', 'idle_1'))
        self.assertEqual(clip.frame_duration, 0.2)
        self.assertTrue(clip.loop)
        with self.assertRaises(AttributeError):
            clip.name = 'changed'

    def test_clip_rejects_invalid_configuration(self):
        with self.assertRaises(ValueError):
            AnimationClip.from_frames('', ['frame'])
        with self.assertRaises(ValueError):
            AnimationClip.from_frames('empty', [])
        with self.assertRaises(ValueError):
            AnimationClip.from_frames('fast', ['frame'], 0)


class SpriteAnimationTests(unittest.TestCase):
    def test_large_delta_advances_multiple_frames_and_keeps_remainder(self):
        animation = SpriteAnimation('walk', ['a', 'b', 'c'], 0.1, loop=True)
        animation.play()

        frame = animation.update(0.25)

        self.assertEqual(frame, 'c')
        self.assertEqual(animation.current_frame, 2)
        self.assertAlmostEqual(animation.frame_timer, 0.05)

    def test_loop_completion_callback_runs_once_per_completed_cycle(self):
        completions = []
        animation = SpriteAnimation(
            'walk',
            [0, 1, 2],
            0.1,
            loop=True,
            on_complete=lambda: completions.append('complete'),
        )
        animation.play()

        animation.update(0.65)

        self.assertEqual(animation.current_frame, 0)
        self.assertAlmostEqual(animation.frame_timer, 0.05)
        self.assertEqual(completions, ['complete', 'complete'])
        self.assertTrue(animation.is_playing)

    def test_non_looping_animation_finishes_on_last_frame_once(self):
        completions = []
        animation = SpriteAnimation(
            'explode',
            ['first', 'last'],
            0.1,
            loop=False,
            on_complete=lambda: completions.append('complete'),
        )
        animation.play()

        frame = animation.update(1.0)
        animation.update(1.0)

        self.assertEqual(frame, 'last')
        self.assertEqual(animation.current_frame_key, 'last')
        self.assertFalse(animation.is_playing)
        self.assertTrue(animation.is_finished)
        self.assertEqual(completions, ['complete'])

    def test_pause_resume_stop_and_reset_have_distinct_behavior(self):
        animation = SpriteAnimation('walk', [0, 1, 2], 0.1)
        animation.play()
        animation.update(0.15)
        animation.pause()

        self.assertEqual(animation.update(1.0), 1)
        self.assertEqual(animation.current_frame, 1)
        self.assertAlmostEqual(animation.frame_timer, 0.05)

        animation.resume()
        self.assertEqual(animation.update(0.05), 2)

        animation.stop()
        self.assertEqual(animation.current_frame, 0)
        self.assertEqual(animation.frame_timer, 0)
        self.assertFalse(animation.is_playing)

    def test_negative_delta_is_rejected(self):
        animation = SpriteAnimation('idle', [0])
        with self.assertRaises(ValueError):
            animation.update(-0.1)

    def test_shared_clip_creates_independent_playback_state(self):
        clip = AnimationClip.from_frames('walk', ['a', 'b'], 0.1)
        first = SpriteAnimation.from_clip(clip)
        second = SpriteAnimation.from_clip(clip)
        first.play()
        second.play()

        first.update(0.1)

        self.assertEqual(first.current_frame_key, 'b')
        self.assertEqual(second.current_frame_key, 'a')
        self.assertIs(first.clip, second.clip)

    def test_replaying_finished_animation_restarts_it(self):
        animation = SpriteAnimation('once', [0, 1], 0.1, loop=False)
        animation.play()
        animation.update(0.2)
        self.assertTrue(animation.is_finished)

        animation.play()

        self.assertEqual(animation.current_frame_key, 0)
        self.assertTrue(animation.is_playing)
        self.assertFalse(animation.is_finished)


if __name__ == '__main__':
    unittest.main()
