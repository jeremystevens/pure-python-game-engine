"""
Main game engine class that orchestrates all systems
"""
from typing import Optional
from .window import Window
from ..assets.asset_manager import AssetManager
from ..scene.scene import Scene
from ..scene.scene_manager import SceneManager
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
        asset_root=None,
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
        self.asset_manager = AssetManager(asset_root)
        
        # Connect input manager to window
        self.window.set_key_press_callback(self.input_manager.on_key_press)
        self.window.set_key_release_callback(self.input_manager.on_key_release)
        self.window.set_mouse_callback(self.input_manager.on_mouse_event)
        
        # Scene management
        self.scene_manager = SceneManager(self, Scene("Default"))
        self._last_scene: Optional[Scene] = None

        # Engine state
        self.delta_time = 0.0
        self.total_time = 0.0
        
        # Delta time smoothing
        self.delta_time_samples = []
        self.max_delta_samples = 10
        self.smoothed_delta_time = 0.0
        
    @property
    def current_scene(self) -> Optional[Scene]:
        """Return the top of the scene stack, or the last active scene once
        the stack has been fully cleared (for example, after shutdown)."""
        scene = self.scene_manager.current_scene
        if scene is not None:
            self._last_scene = scene
            return scene
        return self._last_scene

    @current_scene.setter
    def current_scene(self, scene: Scene):
        """Preserve direct pre-run scene assignment for compatibility."""
        self.scene_manager.set_initial(scene)

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
    
    def register_scene(self, name: str, provider, replace: bool = False):
        """Register a named scene instance or factory."""
        self.scene_manager.register(name, provider, replace)

    def load_scene(self, scene):
        """Queue replacement of the current scene by instance or name."""
        self.scene_manager.replace(scene)

    def push_scene(self, scene):
        """Queue an overlay scene by instance or registered name."""
        self.scene_manager.push(scene)

    def pop_scene(self):
        """Queue removal of the current overlay scene."""
        self.scene_manager.pop()
    
    def run(self):
        """Run the bounded variable-timestep game loop"""
        self.is_running = True

        try:
            self.initialize()
            self.scene_manager.process_pending()
            self.scene_manager.initialize_current()

            while self.is_running and not self.window.should_close():
                self.scene_manager.process_pending()

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

                self.scene_manager.update(self.delta_time)

                self.update(self.delta_time)

                self.window.clear()

                self.scene_manager.render(self.renderer)

                self.render()
                self.window.update()
        finally:
            self.is_running = False
            try:
                self.cleanup()
            finally:
                try:
                    self._last_scene = self.scene_manager.current_scene
                    self.scene_manager.clear()
                finally:
                    try:
                        self.asset_manager.clear()
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