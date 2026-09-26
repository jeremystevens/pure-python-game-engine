
"""
Example demonstrating gamepad support and input mapping profiles
"""
import math
from engine import GameEngine, GameObject, Vector2, Sprite, Scene


class InputTestPlayer(GameObject):
    """Player that works with input profiles and gamepad"""
    
    def __init__(self, name: str = "InputTestPlayer"):
        super().__init__(name)
        self.speed = 200.0
        self.rotation_speed = 3.0
        
        sprite = Sprite(color='#00FF00', size=Vector2(40, 40))
        self.add_component(sprite)
        self.transform.position = Vector2(400, 300)
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if hasattr(self.scene, 'engine'):
            input_manager = self.scene.engine.input_manager
            
            # Use action-based input (works with any profile)
            movement = input_manager.get_action_movement_vector()
            if movement.magnitude > 0:
                self.transform.translate(movement * self.speed * delta_time)
            
            # Action-based rotation
            if input_manager.is_action_pressed("rotate_left"):
                self.transform.rotate(-self.rotation_speed * delta_time)
            if input_manager.is_action_pressed("rotate_right"):
                self.transform.rotate(self.rotation_speed * delta_time)
            
            # Gamepad-specific input
            if input_manager.is_gamepad_connected(0):
                # Use right stick for rotation
                right_stick = input_manager.get_gamepad_stick("right", 0)
                if abs(right_stick.x) > 0.2:  # Dead zone
                    self.transform.rotate(right_stick.x * self.rotation_speed * delta_time)
            
            # Keep in bounds
            pos = self.transform.position
            pos.x = max(20, min(780, pos.x))
            pos.y = max(20, min(580, pos.y))


class InputProfileDemo(GameEngine):
    """Demo showing input profiles and gamepad support"""
    
    def initialize(self):
        """Initialize the demo"""
        # Create test player
        player = InputTestPlayer("TestPlayer")
        self.current_scene.add_object(player)
        self.current_scene.engine = self
        
        # Simulate gamepad connection for testing
        self.input_manager.simulate_gamepad_connection(0)
        
        # Create custom profile
        custom_profile = self.input_manager.create_profile("Custom Controls")
        custom_profile.map_key("move_up", "i")
        custom_profile.map_key("move_down", "k")
        custom_profile.map_key("move_left", "j")
        custom_profile.map_key("move_right", "l")
        custom_profile.map_key("rotate_left", "u")
        custom_profile.map_key("rotate_right", "o")
        custom_profile.map_key("action", "space")
        
        print("Input Profile Demo")
        print("Controls:")
        print("  Current profile:", self.input_manager.get_active_profile().name)
        print("  1 - Default Keyboard (WASD)")
        print("  2 - Arrow Keys")
        print("  3 - Custom Controls (IJKL)")
        print("  4 - Default Gamepad")
        print("  G - Simulate gamepad input")
        print("  ESC - Quit")
        
    def update(self, delta_time: float):
        """Update demo"""
        # Profile switching
        if self.input_manager.is_key_just_pressed('1'):
            self.input_manager.set_active_profile("default_keyboard")
            print("Switched to Default Keyboard profile")
            
        if self.input_manager.is_key_just_pressed('2'):
            self.input_manager.set_active_profile("arrow_keys")
            print("Switched to Arrow Keys profile")
            
        if self.input_manager.is_key_just_pressed('3'):
            self.input_manager.set_active_profile("Custom Controls")
            print("Switched to Custom Controls profile")
            
        if self.input_manager.is_key_just_pressed('4'):
            self.input_manager.set_active_profile("default_gamepad")
            print("Switched to Default Gamepad profile")
        
        # Simulate gamepad input for testing
        if self.input_manager.is_key_just_pressed('g'):
            print("Simulating gamepad button press...")
            self.input_manager.simulate_gamepad_button_press("a", 0)
            
        # Quit
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        
        # Update window title with current profile
        profile_name = self.input_manager.get_active_profile().name
        fps = self.get_fps()
        self.window.set_title(f"Input Demo - Profile: {profile_name} - FPS: {fps:.1f}")


if __name__ == "__main__":
    demo = InputProfileDemo("Input Profile Demo", (800, 600), 60)
    demo.run()
