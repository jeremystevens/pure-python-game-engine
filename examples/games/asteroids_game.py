
"""
Classic Asteroids Game - 1980s Arcade Style
Built using the Pure Python 2D Game Engine
"""
import math
import random
from typing import List
from engine import GameEngine, GameObject, Vector2, Sprite, SoundGenerator
from engine.scene.game_object import Component


class Ship(GameObject):
    """Player ship with thrust, rotation, and shooting"""
    
    def __init__(self):
        super().__init__("Ship")
        self.velocity = Vector2.zero()
        self.thrust_power = 200.0
        self.rotation_speed = 4.0
        self.max_speed = 300.0
        self.drag = 0.98
        
        # Ship appearance - classic triangular ship
        sprite = Sprite(color='#FFFFFF', size=Vector2(20, 20))
        self.add_component(sprite)
        
        # Start in center of screen
        self.transform.position = Vector2(400, 300)
        
        # Shooting
        self.shoot_cooldown = 0.0
        self.shoot_delay = 0.15
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if not hasattr(self, 'engine'):
            return
            
        input_mgr = self.engine.input_manager
        
        # Rotation
        if input_mgr.is_key_pressed('left') or input_mgr.is_key_pressed('a'):
            self.transform.rotate(-self.rotation_speed * delta_time)
        if input_mgr.is_key_pressed('right') or input_mgr.is_key_pressed('d'):
            self.transform.rotate(self.rotation_speed * delta_time)
        
        # Thrust
        if input_mgr.is_key_pressed('up') or input_mgr.is_key_pressed('w'):
            # Calculate thrust direction based on ship rotation
            thrust_dir = Vector2(0, -1).rotate(self.transform.rotation)
            self.velocity += thrust_dir * self.thrust_power * delta_time
            
            # Limit max speed
            if self.velocity.magnitude > self.max_speed:
                self.velocity = self.velocity.normalize() * self.max_speed
            
            # Play engine sound effect
            if hasattr(self, 'engine') and hasattr(self.engine, 'sound_generator'):
                self.engine.sound_generator.play_sound("engine")
        
        # Apply drag
        self.velocity *= self.drag
        
        # Move ship
        self.transform.translate(self.velocity * delta_time)
        
        # Screen wrapping
        self._wrap_around_screen()
        
        # Shooting
        self.shoot_cooldown -= delta_time
        if (input_mgr.is_key_pressed('space') or input_mgr.is_key_pressed('ctrl')) and self.shoot_cooldown <= 0:
            self._shoot()
            self.shoot_cooldown = self.shoot_delay
    
    def _wrap_around_screen(self):
        """Wrap ship around screen edges"""
        pos = self.transform.position
        if pos.x < 0:
            pos.x = 800
        elif pos.x > 800:
            pos.x = 0
        if pos.y < 0:
            pos.y = 600
        elif pos.y > 600:
            pos.y = 0
    
    def _shoot(self):
        """Create a bullet"""
        if hasattr(self, 'engine') and self.engine.current_scene:
            bullet = Bullet()
            bullet.transform.position = self.transform.position.copy()
            bullet.transform.rotation = self.transform.rotation
            
            # Bullet velocity based on ship direction and velocity
            direction = Vector2(0, -1).rotate(self.transform.rotation)
            bullet.velocity = direction * 400 + self.velocity * 0.5
            
            bullet.engine = self.engine
            self.engine.current_scene.add_object(bullet)
            
            # Play bullet sound effect
            if hasattr(self.engine, 'sound_generator'):
                self.engine.sound_generator.play_sound("bullet")
    
    def render(self, renderer):
        """Custom render for triangular ship"""
        # Draw ship as triangle pointing in rotation direction
        ship_points = [
            Vector2(0, -10),   # Nose
            Vector2(-8, 8),    # Left wing
            Vector2(8, 8)      # Right wing
        ]
        
        # Rotate points based on ship rotation
        rotated_points = []
        for point in ship_points:
            rotated = point.rotate(self.transform.rotation)
            world_pos = self.transform.position + rotated
            rotated_points.append(world_pos)
        
        renderer.draw_polygon(rotated_points, '#FFFFFF', outline='#FFFFFF', width=2)


class Bullet(GameObject):
    """Ship bullet projectile"""
    
    def __init__(self):
        super().__init__("Bullet")
        self.velocity = Vector2.zero()
        self.lifetime = 2.0  # Bullets disappear after 2 seconds
        
        sprite = Sprite(color='#FFFFFF', size=Vector2(3, 3))
        self.add_component(sprite)
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move bullet
        self.transform.translate(self.velocity * delta_time)
        
        # Screen wrapping
        self._wrap_around_screen()
        
        # Lifetime
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.destroy()
        
        # Check collision with asteroids
        if hasattr(self, 'engine'):
            self._check_asteroid_collision()
    
    def _wrap_around_screen(self):
        """Wrap bullet around screen edges"""
        pos = self.transform.position
        if pos.x < 0:
            pos.x = 800
        elif pos.x > 800:
            pos.x = 0
        if pos.y < 0:
            pos.y = 600
        elif pos.y > 600:
            pos.y = 0
    
    def _check_asteroid_collision(self):
        """Check if bullet hits an asteroid"""
        if not self.engine.current_scene:
            return
            
        asteroids = [obj for obj in self.engine.current_scene.game_objects 
                    if isinstance(obj, Asteroid) and not obj.is_destroyed]
        
        for asteroid in asteroids:
            distance = self.transform.position.distance_to(asteroid.transform.position)
            # Use radius for collision detection (asteroid.size is diameter-like)
            asteroid_radius = asteroid.size * 0.4
            bullet_radius = 2  # Small bullet radius
            collision_distance = asteroid_radius + bullet_radius
            
            if distance < collision_distance:
                # Hit! Destroy bullet and asteroid
                self.destroy()
                asteroid.destroy()
                
                # Play explosion sound
                if hasattr(self.engine, 'sound_generator'):
                    self.engine.sound_generator.play_sound("explosion")
                
                # Add score
                if hasattr(self.engine.current_scene, 'score'):
                    points = 20 if asteroid.size > 30 else 50 if asteroid.size > 15 else 100
                    self.engine.current_scene.score += points
                
                # Create smaller asteroids if this was a large one
                if asteroid.size > 15:
                    asteroid._split()
                break


class Asteroid(GameObject):
    """Floating space rock"""
    
    def __init__(self, size: float = 40.0, position: Vector2 = None):
        super().__init__("Asteroid")
        self.size = size
        self.velocity = Vector2.zero()
        self.rotation_speed = random.uniform(-2.0, 2.0)
        
        # Random velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(20, 80)
        self.velocity = Vector2.from_angle(angle, speed)
        
        # Position
        if position:
            self.transform.position = position
        else:
            self._spawn_at_edge()
        
        # Appearance
        sprite = Sprite(color='#AAAAAA', size=Vector2(size, size))
        self.add_component(sprite)
        
        # Generate random asteroid shape
        self.vertices = self._generate_shape()
        
    def _spawn_at_edge(self):
        """Spawn asteroid at screen edge"""
        edge = random.randint(0, 3)
        if edge == 0:  # Top
            self.transform.position = Vector2(random.uniform(0, 800), -self.size)
        elif edge == 1:  # Right
            self.transform.position = Vector2(800 + self.size, random.uniform(0, 600))
        elif edge == 2:  # Bottom
            self.transform.position = Vector2(random.uniform(0, 800), 600 + self.size)
        else:  # Left
            self.transform.position = Vector2(-self.size, random.uniform(0, 600))
    
    def _generate_shape(self):
        """Generate random asteroid shape"""
        vertices = []
        num_points = random.randint(8, 12)
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            # Random radius variation
            radius = self.size * random.uniform(0.6, 1.0)
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            vertices.append(Vector2(x, y))
        
        return vertices
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move asteroid
        self.transform.translate(self.velocity * delta_time)
        
        # Rotate
        self.transform.rotate(self.rotation_speed * delta_time)
        
        # Screen wrapping
        self._wrap_around_screen()
        
        # Check collision with ship
        if hasattr(self, 'engine'):
            self._check_ship_collision()
    
    def _wrap_around_screen(self):
        """Wrap asteroid around screen edges"""
        pos = self.transform.position
        margin = self.size
        if pos.x < -margin:
            pos.x = 800 + margin
        elif pos.x > 800 + margin:
            pos.x = -margin
        if pos.y < -margin:
            pos.y = 600 + margin
        elif pos.y > 600 + margin:
            pos.y = -margin
    
    def _check_ship_collision(self):
        """Check if asteroid hits the ship"""
        if not self.engine.current_scene:
            return
            
        ship = self.engine.current_scene.find_object("Ship")
        if ship and not ship.is_destroyed:
            distance = self.transform.position.distance_to(ship.transform.position)
            # Use proper radius calculations for collision
            asteroid_radius = self.size * 0.5  # Half the size since size is diameter-like
            ship_radius = 15  # Ship collision radius (accounting for triangular ship size)
            collision_distance = asteroid_radius + ship_radius
            
            if distance < collision_distance:
                # Ship destroyed!
                if hasattr(self.engine.current_scene, 'game_over_callback'):
                    self.engine.current_scene.game_over_callback()
    
    def _split(self):
        """Split asteroid into smaller pieces"""
        if not hasattr(self, 'engine') or not self.engine.current_scene:
            return
            
        if self.size > 15:  # Only split if large enough
            # Create 2-3 smaller asteroids
            num_pieces = random.randint(2, 3)
            new_size = self.size * 0.6
            
            for i in range(num_pieces):
                new_asteroid = Asteroid(new_size, self.transform.position.copy())
                # Give them random velocities
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(40, 120)
                new_asteroid.velocity = Vector2.from_angle(angle, speed)
                new_asteroid.engine = self.engine
                self.engine.current_scene.add_object(new_asteroid)
    
    def render(self, renderer):
        """Custom render for irregular asteroid shape"""
        # Transform vertices to world space
        world_vertices = []
        for vertex in self.vertices:
            rotated = vertex.rotate(self.transform.rotation)
            world_pos = self.transform.position + rotated
            world_vertices.append(world_pos)
        
        renderer.draw_polygon(world_vertices, outline='#AAAAAA', color='', width=2)


class AsteroidsGame(GameEngine):
    """Main Asteroids game class"""
    
    def __init__(self):
        super().__init__("Asteroids - 1980s Arcade Classic", (800, 600), 60)
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.wave = 1
        self.ship = None
        
        # Initialize sound system
        self.sound_generator = SoundGenerator()
        self.sound_generator.initialize_default_sounds()
        
    def initialize(self):
        """Initialize the game"""
        # Create player ship
        self.ship = Ship()
        self.ship.engine = self
        self.current_scene.add_object(self.ship)
        
        # Set up scene callbacks
        self.current_scene.score = 0
        self.current_scene.game_over_callback = self._game_over
        
        # Spawn initial asteroids
        self._spawn_asteroid_wave()
        
        print("ASTEROIDS - 1980s Arcade Classic")
        print("Controls:")
        print("  Left/Right or A/D - Rotate ship")
        print("  Up or W - Thrust")
        print("  Space or Ctrl - Shoot")
        print("  ESC - Quit")
        print("")
        print("Destroy all asteroids to advance to the next wave!")
        print("Watch out - large asteroids split into smaller ones!")
        print("")
        print("🔊 Procedural sound effects enabled!")
        print("Listen for: bullet shots, explosions, and engine thrust")
    
    def update(self, delta_time: float):
        """Game update logic"""
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        
        if not self.game_over:
            # Update score from scene
            if hasattr(self.current_scene, 'score'):
                self.score = self.current_scene.score
            
            # Check if all asteroids are destroyed
            asteroids = [obj for obj in self.current_scene.game_objects 
                        if isinstance(obj, Asteroid) and not obj.is_destroyed]
            
            if len(asteroids) == 0:
                self._next_wave()
        else:
            # Game over - restart on space
            if self.input_manager.is_key_just_pressed('space'):
                self._restart_game()
    
    def render(self):
        """Custom rendering for UI"""
        # Draw score
        self.renderer.draw_text(
            Vector2(100, 30), 
            f"SCORE: {self.score:06d}", 
            '#FFFFFF', 
            16, 
            'center'
        )
        
        # Draw lives
        self.renderer.draw_text(
            Vector2(700, 30), 
            f"LIVES: {self.lives}", 
            '#FFFFFF', 
            16, 
            'center'
        )
        
        # Draw wave
        self.renderer.draw_text(
            Vector2(400, 30), 
            f"WAVE {self.wave}", 
            '#FFFFFF', 
            16, 
            'center'
        )
        
        if self.game_over:
            # Game over screen
            self.renderer.draw_text(
                Vector2(400, 250), 
                "GAME OVER", 
                '#FF0000', 
                32, 
                'center'
            )
            self.renderer.draw_text(
                Vector2(400, 300), 
                f"FINAL SCORE: {self.score:06d}", 
                '#FFFFFF', 
                20, 
                'center'
            )
            self.renderer.draw_text(
                Vector2(400, 350), 
                "PRESS SPACE TO RESTART", 
                '#FFFFFF', 
                16, 
                'center'
            )
    
    def _spawn_asteroid_wave(self):
        """Spawn a wave of asteroids"""
        # Number of asteroids increases each wave
        num_asteroids = 4 + self.wave
        
        for i in range(num_asteroids):
            asteroid = Asteroid()
            asteroid.engine = self
            self.current_scene.add_object(asteroid)
    
    def _next_wave(self):
        """Advance to next wave"""
        self.wave += 1
        
        # Bonus points for completing wave
        self.score += 1000
        self.current_scene.score = self.score
        
        print(f"Wave {self.wave} complete! Bonus: 1000 points")
        
        # Spawn new asteroids
        self._spawn_asteroid_wave()
    
    def _game_over(self):
        """Handle ship destruction"""
        self.lives -= 1
        
        if self.lives > 0:
            # Respawn ship if lives remaining
            print(f"Ship destroyed! Lives remaining: {self.lives}")
            
            # Remove ship and create new one
            if self.ship:
                self.ship.destroy()
            
            self.ship = Ship()
            self.ship.engine = self
            self.current_scene.add_object(self.ship)
        else:
            # Game over
            self.game_over = True
            print(f"Game Over! Final Score: {self.score:06d}")
    
    def _restart_game(self):
        """Restart the game"""
        # Clear scene
        self.current_scene.cleanup()
        
        # Reset game state
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.wave = 1
        
        # Reinitialize
        self.current_scene.score = 0
        self.current_scene.game_over_callback = self._game_over
        
        # Create new ship
        self.ship = Ship()
        self.ship.engine = self
        self.current_scene.add_object(self.ship)
        
        # Spawn asteroids
        self._spawn_asteroid_wave()
        
        print("Game restarted!")


if __name__ == "__main__":
    game = AsteroidsGame()
    game.run()
