
"""
Example demonstrating the ECS (Entity Component System) architecture
"""
from engine import GameEngine, Vector2
from engine.ecs.components import (
    HealthComponent,
    SpriteComponent,
    TagComponent,
    TransformComponent,
    VelocityComponent,
)
from engine.ecs.entity import Entity
from engine.ecs.systems import BoundarySystem, HealthSystem, MovementSystem, RenderSystem
from engine.ecs.world import World
import random
import math


class ECSGame(GameEngine):
    """ECS-based game example"""
    
    def initialize(self):
        """Initialize the ECS world and create entities"""
        # Create ECS world
        self.world = World()
        
        # Add systems
        self.world.add_system(MovementSystem(priority=100))
        self.world.add_system(BoundarySystem(self.size[0], self.size[1], wrap_around=True, priority=150))
        self.world.add_system(RenderSystem(self.renderer, priority=1000))
        self.world.add_system(HealthSystem(priority=200))
        
        # Create player entity
        self.create_player()
        
        # Create enemy entities
        for i in range(5):
            self.create_enemy(i)
        
        # Create some floating objects
        for i in range(10):
            self.create_floating_object(i)
        
        print("ECS Demo - Pure ECS Architecture")
        print("Controls:")
        print("  WASD or Arrow Keys - Move player (blue square)")
        print("  ESC - Quit")
        print("Features:")
        print("  - Entities are data containers")
        print("  - Components hold data")
        print("  - Systems process entities with specific components")
        print("  - Red enemies move in patterns")
        print("  - Green objects float randomly")
        print("  - All objects wrap around screen boundaries")
    
    def create_player(self):
        """Create player entity with ECS components"""
        player = self.world.create_entity("player")
        
        # Add components
        self.world.add_component(player, TransformComponent(Vector2(400, 300)))
        self.world.add_component(player, VelocityComponent(Vector2(0, 0), max_speed=300))
        self.world.add_component(player, SpriteComponent('#0096FF', Vector2(40, 40)))
        self.world.add_component(player, HealthComponent(100))
        self.world.add_component(player, TagComponent('player', 'controllable'))
        
        # Store reference for input handling
        self.player_entity = player
    
    def create_enemy(self, index: int):
        """Create enemy entity"""
        enemy = self.world.create_entity(f"enemy_{index}")
        
        # Random position
        pos = Vector2(
            random.uniform(50, self.size[0] - 50),
            random.uniform(50, self.size[1] - 50)
        )
        
        # Circular movement velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 150)
        velocity = Vector2.from_angle(angle, speed)
        
        # Add components
        self.world.add_component(enemy, TransformComponent(pos))
        self.world.add_component(enemy, VelocityComponent(velocity, max_speed=200))
        self.world.add_component(enemy, SpriteComponent('#FF3333', Vector2(30, 30)))
        self.world.add_component(enemy, HealthComponent(50))
        self.world.add_component(enemy, TagComponent('enemy', 'hostile'))
    
    def create_floating_object(self, index: int):
        """Create floating decorative object"""
        obj = self.world.create_entity(f"float_{index}")
        
        # Random position and velocity
        pos = Vector2(
            random.uniform(0, self.size[0]),
            random.uniform(0, self.size[1])
        )
        velocity = Vector2(
            random.uniform(-50, 50),
            random.uniform(-50, 50)
        )
        
        # Add components
        self.world.add_component(obj, TransformComponent(pos))
        self.world.add_component(obj, VelocityComponent(velocity))
        self.world.add_component(obj, SpriteComponent('#00FF88', Vector2(15, 15), 'circle'))
        self.world.add_component(obj, TagComponent('decoration'))
    
    def update(self, delta_time: float):
        """Update game logic"""
        # Handle input for player
        self.handle_player_input(delta_time)
        
        # Update enemy movement patterns
        self.update_enemy_patterns(delta_time)
        
        # Update ECS world
        self.world.update(delta_time)
        
        # Check for quit
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        
        # Update window title with entity count
        entity_count = len(self.world.get_all_entities())
        fps = self.get_fps()
        self.window.set_title(f"ECS Demo - Entities: {entity_count} - FPS: {fps:.1f}")
    
    def handle_player_input(self, delta_time: float):
        """Handle player input using ECS"""
        if hasattr(self, 'player_entity'):
            velocity_comp = self.world.get_component(self.player_entity, VelocityComponent)
            
            if velocity_comp:
                # Get movement input
                movement = self.input_manager.get_movement_vector()
                velocity_comp.velocity = movement * 250  # Base speed
    
    def update_enemy_patterns(self, delta_time: float):
        """Update enemy movement patterns"""
        enemies = self.world.get_entities_with_components(TransformComponent, VelocityComponent, TagComponent)
        
        for enemy in enemies:
            tag_comp = self.world.get_component(enemy, TagComponent)
            if tag_comp and tag_comp.has_tag('enemy'):
                velocity_comp = self.world.get_component(enemy, VelocityComponent)
                transform_comp = self.world.get_component(enemy, TransformComponent)
                
                if velocity_comp and transform_comp:
                    # Add some circular motion
                    current_angle = math.atan2(velocity_comp.velocity.y, velocity_comp.velocity.x)
                    new_angle = current_angle + delta_time * 2.0  # Rotate over time
                    speed = velocity_comp.velocity.magnitude
                    
                    velocity_comp.velocity = Vector2.from_angle(new_angle, speed)


if __name__ == "__main__":
    game = ECSGame("ECS Demo - Pure Component System", (800, 600), 60)
    game.run()
