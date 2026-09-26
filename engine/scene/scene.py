"""
Scene class for managing game objects and game state
"""
from typing import List, Dict, Optional, Any
from .game_object import GameObject
from ..collision.system import CollisionSystem
from ..graphics.renderer import Renderer


class Scene:
    """Scene class for organizing game objects"""
    
    def __init__(self, name: str = "Untitled Scene"):
        self.name = name
        self.game_objects: List[GameObject] = []
        self.objects_by_name: Dict[str, GameObject] = {}
        self.objects_by_tag: Dict[str, List[GameObject]] = {}
        self.is_active = True
        self.data: Dict[str, Any] = {}  # For storing scene-specific data
        self.collision_system = CollisionSystem(self)
        
    def initialize(self):
        """Initialize the scene"""
        for obj in self.game_objects:
            obj.start()
    
    def add_object(self, game_object: GameObject):
        """Add a game object to the scene"""
        if game_object not in self.game_objects:
            self.game_objects.append(game_object)
            game_object.scene = self
            
            # Index by name
            if game_object.name:
                self.objects_by_name[game_object.name] = game_object
            
            # Index by tags
            for tag in game_object.tags:
                if tag not in self.objects_by_tag:
                    self.objects_by_tag[tag] = []
                self.objects_by_tag[tag].append(game_object)
    
    def remove_object(self, game_object: GameObject):
        """Remove a game object from the scene"""
        if game_object in self.game_objects:
            self.game_objects.remove(game_object)
            game_object.scene = None
            
            # Remove from name index
            if game_object.name in self.objects_by_name:
                del self.objects_by_name[game_object.name]
            
            # Remove from tag indices
            for tag in game_object.tags:
                if tag in self.objects_by_tag:
                    if game_object in self.objects_by_tag[tag]:
                        self.objects_by_tag[tag].remove(game_object)
                    if not self.objects_by_tag[tag]:
                        del self.objects_by_tag[tag]
    
    def find_object(self, name: str) -> Optional[GameObject]:
        """Find a game object by name"""
        return self.objects_by_name.get(name)
    
    def find_objects_with_tag(self, tag: str) -> List[GameObject]:
        """Find all game objects with a specific tag"""
        return self.objects_by_tag.get(tag, []).copy()
    
    def find_objects_of_type(self, object_type: type) -> List[GameObject]:
        """Find all game objects of a specific type"""
        return [obj for obj in self.game_objects if isinstance(obj, object_type)]
    
    def update(self, delta_time: float):
        """Update all game objects in the scene"""
        if not self.is_active:
            return
        
        # Update all objects (copy list to handle modifications during iteration)
        for obj in self.game_objects.copy():
            if obj.is_active:
                obj.update(delta_time)

        self.collision_system.update()

        # Remove destroyed objects
        self._cleanup_destroyed_objects()
    
    def render(self, renderer: Renderer):
        """Render all game objects in the scene"""
        if not self.is_active:
            return
        
        # Sort objects by z-order (render order)
        sorted_objects = sorted(
            [obj for obj in self.game_objects if obj.is_active],
            key=lambda obj: obj.z_order
        )
        
        # Render all objects
        for obj in sorted_objects:
            obj.render(renderer)
    
    def _cleanup_destroyed_objects(self):
        """Remove destroyed objects from the scene"""
        destroyed_objects = [obj for obj in self.game_objects if obj.is_destroyed]
        for obj in destroyed_objects:
            self.remove_object(obj)
    
    def cleanup(self):
        """Cleanup the scene"""
        self.collision_system.clear()
        for obj in self.game_objects.copy():
            obj.destroy()
        self.game_objects.clear()
        self.objects_by_name.clear()
        self.objects_by_tag.clear()
    
    def set_active(self, active: bool):
        """Set scene active state"""
        self.is_active = active
    
    def get_object_count(self) -> int:
        """Get the number of objects in the scene"""
        return len(self.game_objects)
    
    def get_active_object_count(self) -> int:
        """Get the number of active objects in the scene"""
        return len([obj for obj in self.game_objects if obj.is_active])