import math
import unittest

from engine.input.input_manager import InputManager, InputProfile
from engine.math.vector2 import Vector2


class InputProfileTests(unittest.TestCase):
    def test_mappings_are_case_normalized(self):
        profile = InputProfile('Custom')

        profile.map_key('jump', 'SPACE')
        profile.map_gamepad_button('jump', 'A')
        profile.map_mouse_button('fire', 'LEFT')

        self.assertEqual(profile.get_key_for_action('jump'), 'space')
        self.assertEqual(profile.get_gamepad_button_for_action('jump'), 'a')
        self.assertEqual(profile.get_mouse_button_for_action('fire'), 'left')
        self.assertIsNone(profile.get_key_for_action('missing'))


class InputManagerTests(unittest.TestCase):
    def setUp(self):
        self.inputs = InputManager()

    def test_keyboard_pressed_and_released_transitions_last_one_frame(self):
        self.inputs.on_key_press('W', 0)
        self.inputs.on_key_press('W', 0)
        self.assertTrue(self.inputs.is_key_pressed('w'))
        self.assertFalse(self.inputs.is_key_just_pressed('w'))

        self.inputs.update()
        self.assertTrue(self.inputs.is_key_just_pressed('w'))

        self.inputs.update()
        self.assertFalse(self.inputs.is_key_just_pressed('w'))

        self.inputs.on_key_release('W', 0)
        self.assertFalse(self.inputs.is_key_pressed('w'))
        self.inputs.update()
        self.assertTrue(self.inputs.is_key_just_released('w'))

        self.inputs.update()
        self.assertFalse(self.inputs.is_key_just_released('w'))

    def test_tk_key_names_are_normalized(self):
        self.inputs.on_key_press('Up', 0)
        self.inputs.on_key_press('Escape', 0)

        self.assertTrue(self.inputs.is_key_pressed('up'))
        self.assertTrue(self.inputs.is_key_pressed('escape'))

    def test_mouse_position_is_returned_as_a_copy(self):
        self.inputs.on_mouse_event('move', 0, 12, 34)

        position = self.inputs.get_mouse_position()
        position.x = 100

        self.assertEqual(self.inputs.get_mouse_position(), Vector2(12, 34))

    def test_mouse_button_pressed_and_released_transitions_last_one_frame(self):
        self.inputs.on_mouse_event('click', 1, 0, 0)
        self.assertTrue(self.inputs.is_mouse_button_pressed('left'))
        self.inputs.update()
        self.assertTrue(self.inputs.is_mouse_button_just_pressed('left'))

        self.inputs.update()
        self.assertFalse(self.inputs.is_mouse_button_just_pressed('left'))

        self.inputs.on_mouse_event('release', 1, 0, 0)
        self.assertFalse(self.inputs.is_mouse_button_pressed('left'))
        self.inputs.update()
        self.assertTrue(self.inputs.is_mouse_button_just_released('left'))

        self.inputs.update()
        self.assertFalse(self.inputs.is_mouse_button_just_released('left'))

    def test_movement_vector_is_normalized_and_prefers_arrows(self):
        self.inputs.on_key_press('Up', 0)
        self.inputs.on_key_press('Right', 0)
        self.inputs.on_key_press('a', 0)

        movement = self.inputs.get_movement_vector()

        self.assertAlmostEqual(movement.x, math.sqrt(0.5))
        self.assertAlmostEqual(movement.y, -math.sqrt(0.5))

    def test_profile_management_and_actions(self):
        profile = self.inputs.create_profile('custom')
        profile.map_key('jump', 'j')
        profile.map_mouse_button('fire', 'right')
        self.inputs.set_active_profile('custom')

        self.inputs.on_key_press('j', 0)
        self.inputs.on_mouse_event('click', 3, 0, 0)
        self.inputs.update()

        self.assertIs(self.inputs.get_active_profile(), profile)
        self.assertIs(self.inputs.get_profile('custom'), profile)
        self.assertIn('custom', self.inputs.list_profiles())
        self.assertTrue(self.inputs.is_action_pressed('jump'))
        self.assertTrue(self.inputs.is_action_just_pressed('jump'))
        self.assertTrue(self.inputs.is_action_pressed('fire'))

    def test_action_movement_uses_active_profile(self):
        self.inputs.set_active_profile('arrow_keys')
        self.inputs.on_key_press('Left', 0)
        self.inputs.on_key_press('Down', 0)

        movement = self.inputs.get_action_movement_vector()

        self.assertAlmostEqual(movement.x, -math.sqrt(0.5))
        self.assertAlmostEqual(movement.y, math.sqrt(0.5))

    def test_gamepad_simulation_tracks_buttons_and_clamps_sticks(self):
        self.assertFalse(self.inputs.is_gamepad_connected())
        self.inputs.simulate_gamepad_connection()
        self.inputs.simulate_gamepad_button_press('a')
        self.inputs.simulate_gamepad_stick_input('left', 2, -2)
        self.inputs.update()

        self.assertTrue(self.inputs.is_gamepad_connected())
        self.assertTrue(self.inputs.is_gamepad_button_pressed('a'))
        self.assertTrue(self.inputs.is_gamepad_button_just_pressed('a'))
        self.assertEqual(self.inputs.get_gamepad_stick('left'), Vector2(1, -1))

        self.inputs.update()
        self.assertFalse(self.inputs.is_gamepad_button_just_pressed('a'))

        self.inputs.simulate_gamepad_button_release('a')
        self.inputs.update()
        self.assertFalse(self.inputs.is_gamepad_button_pressed('a'))
        self.assertTrue(self.inputs.is_gamepad_button_just_released('a'))

        self.inputs.update()
        self.assertFalse(self.inputs.is_gamepad_button_just_released('a'))

    def test_callbacks_can_be_registered_triggered_and_removed(self):
        calls = []
        self.inputs.register_input_callback('jump', lambda height: calls.append(height))

        self.inputs.trigger_callback('jump', 3)
        self.inputs.unregister_input_callback('jump')
        self.inputs.trigger_callback('jump', 4)

        self.assertEqual(calls, [3])


if __name__ == '__main__':
    unittest.main()
