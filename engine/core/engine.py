"""
Main game engine class that orchestrates all systems
"""
from typing import Optional
from .window import Window
from ..scene.scene import Scene
from ..input.input_manager import InputManager
from ..graphics.renderer import Renderer


class GameEngine:
    """Main game engine class"""
    
    def __init__(
        self,
        title: str = "2D Game Engine",
        size: tuple = (800, 600),
        target_fps: int = 60,
        max_delta_time: float = 0.1,
    ):
        """Initialize the game engine"""
        self.title = title
        self.size = size
        self.target_fps = target_fps
        self.max_delta_time = max_delta_time
        self.is_running = False
        
        # Core systems
        self.window = Window(title, size, target_fps, max_delta_time)
        self.input_manager = InputManager()
        self.renderer = Renderer(self.window.canvas)
        
        # Connect input manager to window
        self.window.set_key_press_callback(self.input_manager.on_key_press)
        self.window.set_key_release_callback(self.input_manager.on_key_release)
        self.window.set_mouse_callback(self.input_manager.on_mouse_event)
        
        # Scene management
        self.current_scene: Optional[Scene] = Scene("Default")
        self.next_scene: Optional[Scene] = None
        
        # Engine state
        self.delta_time = 0.0
        self.total_time = 0.0
        
        # Delta time smoothing
        self.delta_time_samples = []
        self.max_delta_samples = 10
        self.smoothed_delta_time = 0.0
        
    def initialize(self):
        """Override this method to initialize your game"""
        pass
    
    def update(self, delta_time: float):
        """Override this method for game logic"""
        pass
    
    def render(self):
        """Override this method for custom rendering"""
        pass
    
    def cleanup(self):
        """Override this method for cleanup"""
        pass
    
    def load_scene(self, scene: Scene):
        """Load a new scene"""
        self.next_scene = scene
    
    def run(self):
        """Run the bounded variable-timestep game loop"""
        self.is_running = True

        try:
            self.initialize()

            if self.current_scene:
                self.current_scene.initialize()

            while self.is_running and not self.window.should_close():
                if self.next_scene:
                    next_scene = self.next_scene
                    self.next_scene = None
                    if self.current_scene:
                        self.current_scene.cleanup()
                    self.current_scene = next_scene
                    self.current_scene.initialize()

                bounded_delta = self.window.delta_time
                self.delta_time_samples.append(bounded_delta)

                if len(self.delta_time_samples) > self.max_delta_samples:
                    self.delta_time_samples.pop(0)

                self.smoothed_delta_time = (
                    sum(self.delta_time_samples) / len(self.delta_time_samples)
                )
                self.delta_time = self.smoothed_delta_time
                self.total_time += self.delta_time

                self.input_manager.update()

                if self.current_scene:
                    self.current_scene.update(self.delta_time)

                self.update(self.delta_time)

                self.window.clear()

                if self.current_scene:
                    self.current_scene.render(self.renderer)

                self.render()
                self.window.update()
        finally:
            self.is_running = False
            try:
                self.cleanup()
            finally:
                try:
                    if self.current_scene:
                        self.current_scene.cleanup()
                finally:
                    self.window.quit()
    
    def quit(self):
        """Quit the game"""
        self.is_running = False
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.window.actual_fps
    
    def get_delta_time(self) -> float:
        """Get delta time in seconds"""
        return self.delta_time
    
    def get_total_time(self) -> float:
        """Get total elapsed time"""
        return self.total_time
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.window.toggle_fullscreen()
    
    def set_vsync(self, enabled: bool):
        """Enable or disable vsync"""
        self.window.set_vsync(enabled)