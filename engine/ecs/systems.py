
"""
Common ECS systems
"""
from .system import System
from .components import TransformComponent, VelocityComponent, SpriteComponent, HealthComponent, TimerComponent
from ..math.vector2 import Vector2


class MovementSystem(System):
    """System that handles movement using velocity"""
    
    def __init__(self, priority: int = 100):
        super().__init__(priority)
    
    def update(self, delta_time: float):
        """Update entity positions based on velocity"""
        entities = self.world.get_entities_with_components(TransformComponent, VelocityComponent)
        
        for entity in entities:
            transform = self.world.get_component(entity, TransformComponent)
            velocity = self.world.get_component(entity, VelocityComponent)
            
            if transform and velocity:
                # Limit speed if max_speed is set
                velocity.limit_speed()
                
                # Update position
                transform.translate(velocity.velocity * delta_time)


class RenderSystem(System):
    """System that handles rendering sprites"""
    
    def __init__(self, renderer, priority: int = 1000):
        super().__init__(priority)
        self.renderer = renderer
    
    def update(self, delta_time: float):
        """Render all visible sprites"""
        entities = self.world.get_entities_with_components(TransformComponent, SpriteComponent)
        
        # Sort by z-order if available
        sorted_entities = sorted(entities, key=lambda e: getattr(e, 'z_order', 0))
        
        for entity in sorted_entities:
            transform = self.world.get_component(entity, TransformComponent)
            sprite = self.world.get_component(entity, SpriteComponent)
            
            if transform and sprite and sprite.visible:
                # Render based on shape
                if sprite.shape == 'circle':
                    self.renderer.draw_circle(transform.position, sprite.size.x / 2, sprite.color)
                elif sprite.shape == 'triangle':
                    half_width = sprite.size.x / 2
                    half_height = sprite.size.y / 2
                    local_points = [
                        Vector2(0, -half_height),
                        Vector2(-half_width, half_height),
                        Vector2(half_width, half_height),
                    ]
                    world_points = [
                        transform.position + point.rotate(transform.rotation)
                        for point in local_points
                    ]
                    self.renderer.draw_polygon(world_points, sprite.color)
                else:  # rectangle
                    self.renderer.draw_rectangle(transform.position, sprite.size, sprite.color, transform.rotation)


class HealthSystem(System):
    """System that handles health and death"""
    
    def __init__(self, priority: int = 200):
        super().__init__(priority)
    
    def update(self, delta_time: float):
        """Update health components and handle death"""
        entities = self.world.get_entities_with_component(HealthComponent)
        
        entities_to_destroy = []
        
        for entity in entities:
            health = self.world.get_component(entity, HealthComponent)
            
            if health and health.is_dead:
                entities_to_destroy.append(entity)
        
        # Destroy dead entities
        for entity in entities_to_destroy:
            self.world.destroy_entity(entity)


class TimerSystem(System):
    """System that handles timer components"""
    
    def __init__(self, priority: int = 50):
        super().__init__(priority)
    
    def update(self, delta_time: float):
        """Update all timers"""
        entities = self.world.get_entities_with_component(TimerComponent)
        
        for entity in entities:
            timer = self.world.get_component(entity, TimerComponent)
            if timer:
                timer.update(delta_time)


class BoundarySystem(System):
    """System that keeps entities within screen boundaries"""
    
    def __init__(self, screen_width: int = 800, screen_height: int = 600, wrap_around: bool = True, priority: int = 150):
        super().__init__(priority)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.wrap_around = wrap_around
    
    def update(self, delta_time: float):
        """Keep entities within boundaries"""
        entities = self.world.get_entities_with_component(TransformComponent)
        
        for entity in entities:
            transform = self.world.get_component(entity, TransformComponent)
            
            if transform:
                pos = transform.position
                
                if self.wrap_around:
                    # Wrap around screen
                    if pos.x < 0:
                        pos.x = self.screen_width
                    elif pos.x > self.screen_width:
                        pos.x = 0
                    
                    if pos.y < 0:
                        pos.y = self.screen_height
                    elif pos.y > self.screen_height:
                        pos.y = 0
                else:
                    # Clamp to boundaries
                    pos.x = max(0, min(self.screen_width, pos.x))
                    pos.y = max(0, min(self.screen_height, pos.y))
