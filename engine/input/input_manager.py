"""
Input management system for handling keyboard, mouse, and gamepad input
"""
from typing import Set, Dict, Tuple, Optional, Callable
from ..math.vector2 import Vector2
import time


class GamepadState:
    """Represents the state of a single gamepad"""
    
    def __init__(self, id: int):
        self.id = id
        self.connected = False
        
        # Button states (0-15 for standard gamepad)
        self.buttons_pressed: Set[int] = set()
        self.buttons_just_pressed: Set[int] = set()
        self.buttons_just_released: Set[int] = set()
        self.previous_buttons: Set[int] = set()
        
        # Analog stick values (-1.0 to 1.0)
        self.left_stick = Vector2.zero()
        self.right_stick = Vector2.zero()
        
        # Trigger values (0.0 to 1.0)
        self.left_trigger = 0.0
        self.right_trigger = 0.0
        
        # D-pad state
        self.dpad_up = False
        self.dpad_down = False
        self.dpad_left = False
        self.dpad_right = False
        
        # Standard button mapping
        self.button_names = {
            0: 'a', 1: 'b', 2: 'x', 3: 'y',
            4: 'left_bumper', 5: 'right_bumper',
            6: 'back', 7: 'start',
            8: 'left_stick_button', 9: 'right_stick_button'
        }


class InputProfile:
    """Input mapping profile for customizable controls"""
    
    def __init__(self, name: str):
        self.name = name
        self.key_mappings: Dict[str, str] = {}
        self.gamepad_mappings: Dict[str, str] = {}
        self.mouse_mappings: Dict[str, str] = {}
        
    def map_key(self, action: str, key: str):
        """Map an action to a keyboard key"""
        self.key_mappings[action] = key.lower()
        
    def map_gamepad_button(self, action: str, button: str):
        """Map an action to a gamepad button"""
        self.gamepad_mappings[action] = button.lower()
        
    def map_mouse_button(self, action: str, button: str):
        """Map an action to a mouse button"""
        self.mouse_mappings[action] = button.lower()
        
    def get_key_for_action(self, action: str) -> Optional[str]:
        """Get the key mapped to an action"""
        return self.key_mappings.get(action)
        
    def get_gamepad_button_for_action(self, action: str) -> Optional[str]:
        """Get the gamepad button mapped to an action"""
        return self.gamepad_mappings.get(action)
        
    def get_mouse_button_for_action(self, action: str) -> Optional[str]:
        """Get the mouse button mapped to an action"""
        return self.mouse_mappings.get(action)


class InputManager:
    """Handles all input from keyboard and mouse using tkinter events"""

    def __init__(self):
        # Keyboard state
        self.keys_pressed: Set[str] = set()
        self.keys_just_pressed: Set[str] = set()
        self.keys_just_released: Set[str] = set()
        self.previous_keys: Set[str] = set()

        # Mouse state
        self.mouse_position = Vector2.zero()
        self.mouse_buttons_pressed: Set[int] = set()
        self.mouse_buttons_just_pressed: Set[int] = set()
        self.mouse_buttons_just_released: Set[int] = set()
        self.previous_mouse_buttons: Set[int] = set()

        # Gamepad state (support up to 4 controllers)
        self.gamepads: Dict[int, GamepadState] = {}
        for i in range(4):
            self.gamepads[i] = GamepadState(i)

        # Input profiles
        self.profiles: Dict[str, InputProfile] = {}
        self.active_profile: Optional[InputProfile] = None
        self._create_default_profiles()

        # Key mapping for consistent key names
        self.key_map = {
            'Up': 'up',
            'Down': 'down', 
            'Left': 'left',
            'Right': 'right',
            'w': 'w',
            'a': 'a',
            's': 's',
            'd': 'd',
            'q': 'q',
            'e': 'e',
            'space': 'space',
            'Escape': 'escape',
            'F11': 'f11'
        }

        # Frame-specific input events
        self.frame_key_presses: Set[str] = set()
        self.frame_key_releases: Set[str] = set()
        self.frame_mouse_clicks: Set[int] = set()
        self.frame_mouse_releases: Set[int] = set()
        
        # Input event callbacks
        self.input_callbacks: Dict[str, Callable] = {}

    def update(self):
        """Update input state - call this once per frame"""
        # Store previous states
        self.previous_keys = self.keys_pressed.copy()
        self.previous_mouse_buttons = self.mouse_buttons_pressed.copy()

        # Calculate just pressed/released from frame events
        self.keys_just_pressed = self.frame_key_presses.copy()
        self.keys_just_released = self.frame_key_releases.copy()
        self.mouse_buttons_just_pressed = self.frame_mouse_clicks.copy()
        self.mouse_buttons_just_released = self.frame_mouse_releases.copy()

        # Update gamepad states
        for gamepad in self.gamepads.values():
            # In a real implementation, you would poll the actual gamepad here
            # before comparing the current state with the previous frame.
            self._update_gamepad_state(gamepad)
            gamepad.previous_buttons = gamepad.buttons_pressed.copy()

        # Clear frame-specific events
        self.frame_key_presses.clear()
        self.frame_key_releases.clear()
        self.frame_mouse_clicks.clear()
        self.frame_mouse_releases.clear()

    def on_key_press(self, keysym: str, keycode: int):
        """Handle key press events from window"""
        key = self.key_map.get(keysym, keysym.lower())
        if key not in self.keys_pressed:
            self.keys_pressed.add(key)
            self.frame_key_presses.add(key)

    def on_key_release(self, keysym: str, keycode: int):
        """Handle key release events from window"""
        key = self.key_map.get(keysym, keysym.lower())
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
            self.frame_key_releases.add(key)

    def on_mouse_event(self, event_type: str, button: int, x: int, y: int):
        """Handle mouse events from window"""
        if event_type == 'move':
            self.mouse_position = Vector2(x, y)
        elif event_type == 'click':
            if button not in self.mouse_buttons_pressed:
                self.mouse_buttons_pressed.add(button)
                self.frame_mouse_clicks.add(button)
        elif event_type == 'release':
            if button in self.mouse_buttons_pressed:
                self.mouse_buttons_pressed.remove(button)
                self.frame_mouse_releases.add(button)

    # Keyboard methods
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently being held down"""
        return key.lower() in self.keys_pressed

    def is_key_just_pressed(self, key: str) -> bool:
        """Check if a key was just pressed this frame"""
        return key.lower() in self.keys_just_pressed

    def is_key_just_released(self, key: str) -> bool:
        """Check if a key was just released this frame"""
        return key.lower() in self.keys_just_released

    # Mouse methods
    def is_mouse_button_pressed(self, button) -> bool:
        """Check if a mouse button is currently being held down"""
        button_code = self._get_button_code(button)
        return button_code in self.mouse_buttons_pressed

    def is_mouse_button_just_pressed(self, button) -> bool:
        """Check if a mouse button was just pressed this frame"""
        button_code = self._get_button_code(button)
        return button_code in self.mouse_buttons_just_pressed

    def is_mouse_button_just_released(self, button) -> bool:
        """Check if a mouse button was just released this frame"""
        button_code = self._get_button_code(button)
        return button_code in self.mouse_buttons_just_released
    
    def _get_button_code(self, button):
        """Convert button name to button code"""
        if isinstance(button, str):
            button_map = {'left': 1, 'middle': 2, 'right': 3}
            return button_map.get(button.lower(), 1)
        return button

    def get_mouse_position(self) -> Vector2:
        """Get current mouse position"""
        return self.mouse_position.copy()

    # Convenience methods for common keys
    def is_arrow_key_pressed(self) -> Tuple[bool, bool, bool, bool]:
        """Check arrow keys (up, down, left, right)"""
        return (
            self.is_key_pressed('up'),
            self.is_key_pressed('down'),
            self.is_key_pressed('left'),
            self.is_key_pressed('right')
        )

    def is_wasd_pressed(self) -> Tuple[bool, bool, bool, bool]:
        """Check WASD keys (w, a, s, d)"""
        return (
            self.is_key_pressed('w'),
            self.is_key_pressed('a'),
            self.is_key_pressed('s'),
            self.is_key_pressed('d')
        )

    def get_movement_vector(self) -> Vector2:
        """Get normalized movement vector from arrow keys or WASD"""
        movement = Vector2.zero()

        # Check arrow keys
        up, down, left, right = self.is_arrow_key_pressed()
        if up:
            movement.y -= 1
        if down:
            movement.y += 1
        if left:
            movement.x -= 1
        if right:
            movement.x += 1

        # If no arrow keys, check WASD
        if movement.magnitude == 0:
            w, a, s, d = self.is_wasd_pressed()
            if w:
                movement.y -= 1
            if s:
                movement.y += 1
            if a:
                movement.x -= 1
            if d:
                movement.x += 1

        # Normalize for diagonal movement
        if movement.magnitude > 0:
            movement = movement.normalize()

        return movement
    
    def _create_default_profiles(self):
        """Create default input profiles"""
        # Default keyboard profile
        default_kb = InputProfile("Default Keyboard")
        default_kb.map_key("move_up", "w")
        default_kb.map_key("move_down", "s") 
        default_kb.map_key("move_left", "a")
        default_kb.map_key("move_right", "d")
        default_kb.map_key("rotate_left", "q")
        default_kb.map_key("rotate_right", "e")
        default_kb.map_key("action", "space")
        default_kb.map_key("pause", "escape")
        self.profiles["default_keyboard"] = default_kb
        
        # Alternative keyboard profile (arrow keys)
        arrow_kb = InputProfile("Arrow Keys")
        arrow_kb.map_key("move_up", "up")
        arrow_kb.map_key("move_down", "down")
        arrow_kb.map_key("move_left", "left")
        arrow_kb.map_key("move_right", "right")
        arrow_kb.map_key("rotate_left", "q")
        arrow_kb.map_key("rotate_right", "e")
        arrow_kb.map_key("action", "space")
        arrow_kb.map_key("pause", "escape")
        self.profiles["arrow_keys"] = arrow_kb
        
        # Default gamepad profile
        default_gp = InputProfile("Default Gamepad")
        default_gp.map_gamepad_button("action", "a")
        default_gp.map_gamepad_button("back", "b")
        default_gp.map_gamepad_button("special", "x")
        default_gp.map_gamepad_button("menu", "y")
        default_gp.map_gamepad_button("pause", "start")
        self.profiles["default_gamepad"] = default_gp
        
        # Set default active profile
        self.active_profile = default_kb
    
    def _update_gamepad_state(self, gamepad: GamepadState):
        """Update gamepad state (placeholder for actual gamepad polling)"""
        # Calculate just pressed/released buttons
        gamepad.buttons_just_pressed = gamepad.buttons_pressed - gamepad.previous_buttons
        gamepad.buttons_just_released = gamepad.previous_buttons - gamepad.buttons_pressed
        
        # In a real implementation, you would use a library like pygame or pynput
        # to get actual gamepad input. For now, this is a simulation framework.
    
    # Gamepad methods
    def is_gamepad_connected(self, gamepad_id: int = 0) -> bool:
        """Check if a gamepad is connected"""
        return gamepad_id in self.gamepads and self.gamepads[gamepad_id].connected
    
    def is_gamepad_button_pressed(self, button: str, gamepad_id: int = 0) -> bool:
        """Check if a gamepad button is currently pressed"""
        if not self.is_gamepad_connected(gamepad_id):
            return False
            
        gamepad = self.gamepads[gamepad_id]
        
        # Handle named buttons
        for btn_id, btn_name in gamepad.button_names.items():
            if btn_name == button.lower():
                return btn_id in gamepad.buttons_pressed
        
        # Handle numeric buttons
        try:
            button_id = int(button)
            return button_id in gamepad.buttons_pressed
        except ValueError:
            return False
    
    def is_gamepad_button_just_pressed(self, button: str, gamepad_id: int = 0) -> bool:
        """Check if a gamepad button was just pressed this frame"""
        if not self.is_gamepad_connected(gamepad_id):
            return False
            
        gamepad = self.gamepads[gamepad_id]
        
        for btn_id, btn_name in gamepad.button_names.items():
            if btn_name == button.lower():
                return btn_id in gamepad.buttons_just_pressed
        
        try:
            button_id = int(button)
            return button_id in gamepad.buttons_just_pressed
        except ValueError:
            return False
    
    def is_gamepad_button_just_released(self, button: str, gamepad_id: int = 0) -> bool:
        """Check if a gamepad button was just released this frame"""
        if not self.is_gamepad_connected(gamepad_id):
            return False

        gamepad = self.gamepads[gamepad_id]

        for btn_id, btn_name in gamepad.button_names.items():
            if btn_name == button.lower():
                return btn_id in gamepad.buttons_just_released

        try:
            button_id = int(button)
            return button_id in gamepad.buttons_just_released
        except ValueError:
            return False

    def get_gamepad_stick(self, stick: str, gamepad_id: int = 0) -> Vector2:
        """Get gamepad analog stick value"""
        if not self.is_gamepad_connected(gamepad_id):
            return Vector2.zero()
            
        gamepad = self.gamepads[gamepad_id]
        if stick.lower() == "left":
            return gamepad.left_stick.copy()
        elif stick.lower() == "right":
            return gamepad.right_stick.copy()
        return Vector2.zero()
    
    def get_gamepad_trigger(self, trigger: str, gamepad_id: int = 0) -> float:
        """Get gamepad trigger value (0.0 to 1.0)"""
        if not self.is_gamepad_connected(gamepad_id):
            return 0.0
            
        gamepad = self.gamepads[gamepad_id]
        if trigger.lower() == "left":
            return gamepad.left_trigger
        elif trigger.lower() == "right":
            return gamepad.right_trigger
        return 0.0
    
    # Profile management methods
    def set_active_profile(self, profile_name: str):
        """Set the active input profile"""
        if profile_name in self.profiles:
            self.active_profile = self.profiles[profile_name]
    
    def get_active_profile(self) -> Optional[InputProfile]:
        """Get the currently active input profile"""
        return self.active_profile
    
    def create_profile(self, name: str) -> InputProfile:
        """Create a new input profile"""
        profile = InputProfile(name)
        self.profiles[name] = profile
        return profile
    
    def get_profile(self, name: str) -> Optional[InputProfile]:
        """Get a profile by name"""
        return self.profiles.get(name)
    
    def list_profiles(self) -> list:
        """Get list of all profile names"""
        return list(self.profiles.keys())
    
    # Action-based input methods (using active profile)
    def is_action_pressed(self, action: str) -> bool:
        """Check if an action is pressed using the active profile"""
        if not self.active_profile:
            return False
            
        # Check keyboard mapping
        key = self.active_profile.get_key_for_action(action)
        if key and self.is_key_pressed(key):
            return True
            
        # Check gamepad mapping
        button = self.active_profile.get_gamepad_button_for_action(action)
        if button and self.is_gamepad_button_pressed(button):
            return True
            
        # Check mouse mapping
        mouse_btn = self.active_profile.get_mouse_button_for_action(action)
        if mouse_btn and self.is_mouse_button_pressed(mouse_btn):
            return True
            
        return False
    
    def is_action_just_pressed(self, action: str) -> bool:
        """Check if an action was just pressed using the active profile"""
        if not self.active_profile:
            return False
            
        # Check keyboard mapping
        key = self.active_profile.get_key_for_action(action)
        if key and self.is_key_just_pressed(key):
            return True
            
        # Check gamepad mapping
        button = self.active_profile.get_gamepad_button_for_action(action)
        if button and self.is_gamepad_button_just_pressed(button):
            return True
            
        # Check mouse mapping
        mouse_btn = self.active_profile.get_mouse_button_for_action(action)
        if mouse_btn and self.is_mouse_button_just_pressed(mouse_btn):
            return True
            
        return False
    
    def get_action_movement_vector(self) -> Vector2:
        """Get movement vector from action mappings"""
        if not self.active_profile:
            return self.get_movement_vector()  # Fallback to default
            
        movement = Vector2.zero()
        
        if self.is_action_pressed("move_up"):
            movement.y -= 1
        if self.is_action_pressed("move_down"):
            movement.y += 1
        if self.is_action_pressed("move_left"):
            movement.x -= 1
        if self.is_action_pressed("move_right"):
            movement.x += 1
            
        # Also check gamepad left stick
        stick_input = self.get_gamepad_stick("left")
        if stick_input.magnitude > 0.1:  # Dead zone
            movement += stick_input
            
        # Normalize for diagonal movement
        if movement.magnitude > 1:
            movement = movement.normalize()
            
        return movement
    
    # Event callback system
    def register_input_callback(self, event_name: str, callback: Callable):
        """Register a callback for input events"""
        self.input_callbacks[event_name] = callback
    
    def unregister_input_callback(self, event_name: str):
        """Unregister an input callback"""
        if event_name in self.input_callbacks:
            del self.input_callbacks[event_name]
    
    def trigger_callback(self, event_name: str, *args, **kwargs):
        """Trigger a registered callback"""
        if event_name in self.input_callbacks:
            self.input_callbacks[event_name](*args, **kwargs)
    
    # Simulation methods for testing gamepad functionality
    def simulate_gamepad_connection(self, gamepad_id: int = 0):
        """Simulate connecting a gamepad (for testing)"""
        if gamepad_id in self.gamepads:
            self.gamepads[gamepad_id].connected = True
    
    def simulate_gamepad_button_press(self, button: str, gamepad_id: int = 0):
        """Simulate pressing a gamepad button (for testing)"""
        if not self.is_gamepad_connected(gamepad_id):
            return
            
        gamepad = self.gamepads[gamepad_id]
        for btn_id, btn_name in gamepad.button_names.items():
            if btn_name == button.lower():
                gamepad.buttons_pressed.add(btn_id)
                return
                
        try:
            button_id = int(button)
            gamepad.buttons_pressed.add(button_id)
        except ValueError:
            pass
    
    def simulate_gamepad_button_release(self, button: str, gamepad_id: int = 0):
        """Simulate releasing a gamepad button (for testing)"""
        if not self.is_gamepad_connected(gamepad_id):
            return

        gamepad = self.gamepads[gamepad_id]
        for btn_id, btn_name in gamepad.button_names.items():
            if btn_name == button.lower():
                gamepad.buttons_pressed.discard(btn_id)
                return

        try:
            button_id = int(button)
            gamepad.buttons_pressed.discard(button_id)
        except ValueError:
            pass

    def simulate_gamepad_stick_input(self, stick: str, x: float, y: float, gamepad_id: int = 0):
        """Simulate gamepad stick input (for testing)"""
        if not self.is_gamepad_connected(gamepad_id):
            return
            
        gamepad = self.gamepads[gamepad_id]
        stick_vector = Vector2(max(-1.0, min(1.0, x)), max(-1.0, min(1.0, y)))
        
        if stick.lower() == "left":
            gamepad.left_stick = stick_vector
        elif stick.lower() == "right":
            gamepad.right_stick = stick_vector