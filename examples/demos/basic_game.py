"""
Example game demonstrating the Pure Python 2D Game Engine
"""
import math
from engine import GameEngine, GameObject, Vector2, Transform, Sprite


class Player(GameObject):
    """Player game object with movement"""
    
    def __init__(self, name: str = "Player"):
        super().__init__(name)
        self.speed = 200.0  # pixels per second
        self.rotation_speed = 3.0  # radians per second
        
        # Add sprite component with a colored rectangle
        sprite = Sprite(color='#0096FF', size=Vector2(40, 40))  # Blue player
        self.add_component(sprite)
        
        # Set initial position
        self.transform.position = Vector2(400, 300)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Get input from the engine
        if hasattr(self.scene, 'engine'):
            input_manager = self.scene.engine.input_manager
            
            # Movement
            movement = input_manager.get_movement_vector()
            if movement.magnitude > 0:
                self.transform.translate(movement * self.speed * delta_time)
            
            # Rotation
            if input_manager.is_key_pressed('q'):
                self.transform.rotate(-self.rotation_speed * delta_time)
            if input_manager.is_key_pressed('e'):
                self.transform.rotate(self.rotation_speed * delta_time)
            
            # Keep player in bounds
            pos = self.transform.position
            if pos.x < 0:
                pos.x = 800
            elif pos.x > 800:
                pos.x = 0
            if pos.y < 0:
                pos.y = 600
            elif pos.y > 600:
                pos.y = 0


class Enemy(GameObject):
    """Simple enemy that moves in a circle"""
    
    def __init__(self, name: str = "Enemy", center: Vector2 = None, radius: float = 100):
        super().__init__(name)
        self.center = center or Vector2(400, 300)
        self.radius = radius
        self.angle = 0.0
        self.speed = 2.0  # radians per second
        
        # Add sprite component with red color
        sprite = Sprite(color='#FF3232', size=Vector2(30, 30), shape='circle')  # Red enemy
        self.add_component(sprite)
        
        # Set initial position
        self.transform.position = self.center + Vector2(radius, 0)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move in a circle
        self.angle += self.speed * delta_time
        offset = Vector2.from_angle(self.angle, self.radius)
        self.transform.position = self.center + offset
        
        # Rotate to face movement direction
        self.transform.rotation = self.angle + math.pi / 2


class ExampleGame(GameEngine):
    """Example game class"""
    
    def initialize(self):
        """Initialize the game"""
        # Create player
        player = Player("Player")
        self.current_scene.add_object(player)
        
        # Create some enemies
        for i in range(3):
            angle = (i / 3.0) * 2 * math.pi
            center = Vector2(400, 300) + Vector2.from_angle(angle, 150)
            enemy = Enemy(f"Enemy_{i}", center, 50)
            self.current_scene.add_object(enemy)
        
        # Store reference to engine in scene for input access
        self.current_scene.engine = self
        
        print("Pure Python 2D Game Engine - Example Game")
        print("Controls:")
        print("  Arrow keys or WASD - Move player")
        print("  Q/E - Rotate player")
        print("  F11 - Toggle fullscreen")
        print("  V - Toggle VSync")
        print("  ESC or close window - Quit")
    
    def update(self, delta_time: float):
        """Game update logic"""
        # Check for quit
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        
        # Check for fullscreen toggle
        if self.input_manager.is_key_just_pressed('f11'):
            self.toggle_fullscreen()
        
        # Check for vsync toggle
        if self.input_manager.is_key_just_pressed('v'):
            current_vsync = self.window.get_vsync()
            self.set_vsync(not current_vsync)
            print(f"VSync {'enabled' if not current_vsync else 'disabled'}")
        
        # Update window title with FPS
        fps = self.get_fps()
        self.window.set_title(f"Pure Python 2D Game Engine - FPS: {fps:.1f}")


if __name__ == "__main__":
    # Create and run the game
    game = ExampleGame("Pure Python 2D Game Engine", (800, 600), 60)
    game.run()