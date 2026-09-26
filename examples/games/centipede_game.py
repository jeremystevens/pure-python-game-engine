
"""
Centipede - Classic Arcade Game Recreation
Built using the Pure Python 2D Game Engine
Faithful recreation of the original 1981 Atari arcade game
"""
import math
import random
from typing import List, Optional
from engine import GameEngine, GameObject, Vector2, Sprite, SoundGenerator
from engine.scene.game_object import Component


class BugBlaster(GameObject):
    """Player's bug blaster ship"""
    
    def __init__(self):
        super().__init__("BugBlaster")
        self.speed = 200.0
        self.shoot_cooldown = 0.0
        self.shoot_delay = 0.1
        self.lives = 3
        
        # Player area constraints (bottom portion of screen)
        self.min_y = 400  # Can't go above this line
        self.max_y = 580
        self.min_x = 20
        self.max_x = 780
        
        # Green bug blaster sprite
        sprite = Sprite(color='#00FF00', size=Vector2(16, 16))
        self.add_component(sprite)
        
        # Start position
        self.transform.position = Vector2(400, 550)
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        self.shoot_cooldown -= delta_time
        
        if not hasattr(self.scene, 'engine'):
            return
            
        input_manager = self.scene.engine.input_manager
        
        # Movement in all directions within player area
        movement = Vector2.zero()
        if input_manager.is_key_pressed('left') or input_manager.is_key_pressed('a'):
            movement.x = -1
        if input_manager.is_key_pressed('right') or input_manager.is_key_pressed('d'):
            movement.x = 1
        if input_manager.is_key_pressed('up') or input_manager.is_key_pressed('w'):
            movement.y = -1
        if input_manager.is_key_pressed('down') or input_manager.is_key_pressed('s'):
            movement.y = 1
        
        # Normalize diagonal movement
        if movement.magnitude > 0:
            movement = movement.normalize()
            new_pos = self.transform.position + movement * self.speed * delta_time
            
            # Clamp to player area
            new_pos.x = max(self.min_x, min(self.max_x, new_pos.x))
            new_pos.y = max(self.min_y, min(self.max_y, new_pos.y))
            
            self.transform.position = new_pos
        
        # Shooting
        if (input_manager.is_key_pressed('space') or 
            input_manager.is_key_pressed('ctrl')) and self.shoot_cooldown <= 0:
            self._shoot()
            self.shoot_cooldown = self.shoot_delay
    
    def _shoot(self):
        """Fire a dart upward"""
        if hasattr(self.scene, 'engine'):
            dart = Dart()
            dart.transform.position = Vector2(
                self.transform.position.x, 
                self.transform.position.y - 10
            )
            dart.engine = self.scene.engine
            self.scene.add_object(dart)
            
            # Play shooting sound
            if hasattr(self.scene.engine, 'sound_generator'):
                self.scene.engine.sound_generator.play_sound("shoot")


class Dart(GameObject):
    """Player's dart projectile"""
    
    def __init__(self):
        super().__init__("Dart")
        self.velocity = Vector2(0, -400)  # Fast upward movement
        
        # White dart
        sprite = Sprite(color='#FFFFFF', size=Vector2(2, 6))
        self.add_component(sprite)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move dart
        self.transform.position += self.velocity * delta_time
        
        # Remove if off screen
        if self.transform.position.y < -10:
            self.destroy()
        
        # Check collisions
        if hasattr(self.scene, 'engine'):
            self._check_collisions()
    
    def _check_collisions(self):
        """Check dart collisions with enemies and mushrooms"""
        dart_pos = self.transform.position
        
        # Check mushroom collisions
        mushrooms = [obj for obj in self.scene.game_objects 
                    if isinstance(obj, Mushroom) and not obj.is_destroyed]
        
        for mushroom in mushrooms:
            if dart_pos.distance_to(mushroom.transform.position) < 8:
                mushroom.hit()
                self.destroy()
                return
        
        # Check centipede segment collisions
        segments = [obj for obj in self.scene.game_objects 
                   if isinstance(obj, CentipedeSegment) and not obj.is_destroyed]
        
        for segment in segments:
            if dart_pos.distance_to(segment.transform.position) < 8:
                segment.hit()
                self.destroy()
                return
        
        # Check other enemy collisions
        enemies = [obj for obj in self.scene.game_objects 
                  if isinstance(obj, (Flea, Spider, Scorpion)) and not obj.is_destroyed]
        
        for enemy in enemies:
            if dart_pos.distance_to(enemy.transform.position) < 10:
                enemy.hit()
                self.destroy()
                return


class Mushroom(GameObject):
    """Mushroom obstacle"""
    
    def __init__(self, x, y):
        super().__init__("Mushroom")
        self.hits = 0
        self.max_hits = 4
        self.is_poisoned = False
        self.points = 1
        
        self.transform.position = Vector2(x, y)
        self._update_sprite()
    
    def _update_sprite(self):
        """Update sprite based on damage state"""
        if self.is_poisoned:
            color = '#FF00FF'  # Magenta for poisoned
        else:
            # Different colors based on damage
            colors = ['#00FF00', '#FFFF00', '#FF8000', '#FF0000']  # Green to red
            color = colors[min(self.hits, 3)]
        
        size = Vector2(12, 12)
        sprite = Sprite(color=color, size=size)
        
        # Remove old sprite if exists
        old_sprite = self.get_component(Sprite)
        if old_sprite:
            self.remove_component(Sprite)
        
        self.add_component(sprite)
    
    def hit(self):
        """Mushroom is hit by dart"""
        if self.is_destroyed:
            return
            
        self.hits += 1
        
        if self.hits >= self.max_hits:
            # Award points and destroy
            if hasattr(self.scene, 'engine'):
                self.scene.engine.score += self.points
            self.destroy()
        else:
            self._update_sprite()
    
    def poison(self):
        """Turn mushroom into poison mushroom"""
        self.is_poisoned = True
        self._update_sprite()
    
    def heal(self):
        """Regenerate mushroom (when player dies)"""
        self.hits = 0
        self.is_poisoned = False
        self._update_sprite()


class CentipedeSegment(GameObject):
    """Individual centipede segment"""
    
    def __init__(self, is_head=False):
        super().__init__("CentipedeSegment")
        self.is_head = is_head
        self.speed = 50.0
        self.direction = Vector2(1, 0)  # Start moving right
        self.descent_distance = 16  # How far to move down when turning
        self.is_descending = False
        self.descend_progress = 0.0
        self.is_poisoned_descent = False
        
        # Different colors for head vs body
        color = '#FFFF00' if is_head else '#FF8000'  # Yellow head, orange body
        sprite = Sprite(color=color, size=Vector2(12, 12))
        self.add_component(sprite)
        
        # Grid-based movement
        self.grid_x = 0
        self.grid_y = 0
        self.grid_size = 16
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if self.is_descending:
            self._handle_descent(delta_time)
        else:
            self._handle_horizontal_movement(delta_time)
        
        # Check if reached player area
        if self.transform.position.y > 400:
            self._enter_player_area()
    
    def _handle_horizontal_movement(self, delta_time: float):
        """Handle normal left-right movement"""
        move_distance = self.speed * delta_time
        new_pos = self.transform.position + self.direction * move_distance
        
        # Check for obstacles or screen edges
        if (new_pos.x <= 16 or new_pos.x >= 784 or 
            self._check_mushroom_collision(new_pos)):
            self._start_descent()
        else:
            self.transform.position = new_pos
    
    def _handle_descent(self, delta_time: float):
        """Handle downward movement when turning"""
        self.descend_progress += self.speed * 2 * delta_time
        
        if self.descend_progress >= self.descent_distance:
            # Finished descending
            self.is_descending = False
            self.descend_progress = 0.0
            self.direction.x = -self.direction.x  # Reverse direction
            
            if self.is_poisoned_descent:
                self.is_poisoned_descent = False
        else:
            # Continue descending
            self.transform.position.y += self.speed * 2 * delta_time
    
    def _start_descent(self):
        """Start descending one level"""
        self.is_descending = True
        self.descend_progress = 0.0
    
    def _check_mushroom_collision(self, new_pos):
        """Check if new position would collide with mushroom"""
        if not hasattr(self.scene, 'game_objects'):
            return False
            
        mushrooms = [obj for obj in self.scene.game_objects 
                    if isinstance(obj, Mushroom) and not obj.is_destroyed]
        
        for mushroom in mushrooms:
            distance = new_pos.distance_to(mushroom.transform.position)
            if distance < 12:
                # Check if it's a poison mushroom
                if mushroom.is_poisoned:
                    self._start_poison_descent()
                return True
        return False
    
    def _start_poison_descent(self):
        """Start poison descent - straight down"""
        self.direction = Vector2(0, 1)
        self.is_poisoned_descent = True
        self.is_descending = False  # Don't use normal descent behavior
    
    def _enter_player_area(self):
        """Behavior when centipede enters player area"""
        # In player area, move more erratically
        if not hasattr(self, 'in_player_area'):
            self.in_player_area = True
            self.speed *= 0.7  # Slower in player area
    
    def hit(self):
        """Segment is hit by dart"""
        if self.is_destroyed:
            return
            
        # Award points
        points = 100 if self.is_head else 10
        if hasattr(self.scene, 'engine'):
            self.scene.engine.score += points
        
        # Create mushroom at this position
        mushroom = Mushroom(self.transform.position.x, self.transform.position.y)
        self.scene.add_object(mushroom)
        
        # Play hit sound
        if hasattr(self.scene, 'engine') and hasattr(self.scene.engine, 'sound_generator'):
            self.scene.engine.sound_generator.play_sound("hit")
        
        # Split centipede if this is a middle segment
        if hasattr(self.scene, 'engine'):
            self.scene.engine._split_centipede_at_segment(self)
        
        self.destroy()


class Flea(GameObject):
    """Flea enemy that drops vertically"""
    
    def __init__(self):
        super().__init__("Flea")
        self.speed = 100.0
        self.hits_required = 2
        self.hits_taken = 0
        self.mushroom_drop_chance = 0.3
        self.points = 200
        
        # Purple flea
        sprite = Sprite(color='#8A2BE2', size=Vector2(8, 8))
        self.add_component(sprite)
        
        # Start at random position at top
        self.transform.position = Vector2(random.randint(50, 750), -10)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move down
        self.transform.position.y += self.speed * delta_time
        
        # Randomly drop mushrooms
        if (random.random() < self.mushroom_drop_chance * delta_time and 
            self.transform.position.y > 50):
            mushroom = Mushroom(self.transform.position.x, self.transform.position.y)
            self.scene.add_object(mushroom)
        
        # Remove when off screen
        if self.transform.position.y > 610:
            self.destroy()
    
    def hit(self):
        """Flea is hit by dart"""
        self.hits_taken += 1
        
        if self.hits_taken >= self.hits_required:
            # Award points and destroy
            if hasattr(self.scene, 'engine'):
                self.scene.engine.score += self.points
            self.destroy()


class Spider(GameObject):
    """Spider enemy that moves in zigzag pattern"""
    
    def __init__(self):
        super().__init__("Spider")
        self.speed = 80.0
        self.direction = Vector2(1, 0)
        self.zigzag_timer = 0.0
        self.zigzag_interval = 0.5
        self.points_base = 300
        
        # Red spider
        sprite = Sprite(color='#FF0000', size=Vector2(10, 10))
        self.add_component(sprite)
        
        # Start at side of screen in player area
        side = random.choice([-1, 1])
        start_x = 50 if side > 0 else 750
        self.transform.position = Vector2(start_x, random.randint(450, 550))
        self.direction.x = -side
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        self.zigzag_timer += delta_time
        
        # Zigzag movement
        if self.zigzag_timer >= self.zigzag_interval:
            self.direction.y = random.choice([-1, 0, 1]) * 0.5
            self.zigzag_timer = 0.0
        
        # Move spider
        movement = self.direction.normalize() * self.speed * delta_time
        self.transform.position += movement
        
        # Eat mushrooms
        self._eat_nearby_mushrooms()
        
        # Remove when off screen
        if (self.transform.position.x < -20 or self.transform.position.x > 820 or
            self.transform.position.y < 400 or self.transform.position.y > 600):
            self.destroy()
    
    def _eat_nearby_mushrooms(self):
        """Eat mushrooms that spider touches"""
        if not hasattr(self.scene, 'game_objects'):
            return
            
        mushrooms = [obj for obj in self.scene.game_objects 
                    if isinstance(obj, Mushroom) and not obj.is_destroyed]
        
        for mushroom in mushrooms:
            distance = self.transform.position.distance_to(mushroom.transform.position)
            if distance < 10:
                mushroom.destroy()
                break
    
    def hit(self):
        """Spider is hit by dart"""
        # Award points based on distance from player
        if hasattr(self.scene, 'engine'):
            player = self.scene.find_object("BugBlaster")
            if player:
                distance = self.transform.position.distance_to(player.transform.position)
                if distance < 50:
                    points = self.points_base * 3  # 900 points
                elif distance < 100:
                    points = self.points_base * 2  # 600 points
                else:
                    points = self.points_base  # 300 points
                
                self.scene.engine.score += points
        
        self.destroy()


class Scorpion(GameObject):
    """Scorpion enemy that poisons mushrooms"""
    
    def __init__(self):
        super().__init__("Scorpion")
        self.speed = 60.0
        self.direction = Vector2(1, 0)
        self.points = 1000
        
        # Cyan scorpion
        sprite = Sprite(color='#00FFFF', size=Vector2(14, 8))
        self.add_component(sprite)
        
        # Start at random side
        side = random.choice([-1, 1])
        start_x = -20 if side > 0 else 820
        self.transform.position = Vector2(start_x, random.randint(100, 300))
        self.direction.x = side
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move horizontally
        self.transform.position += self.direction * self.speed * delta_time
        
        # Poison mushrooms
        self._poison_nearby_mushrooms()
        
        # Remove when off screen
        if (self.transform.position.x < -30 or self.transform.position.x > 830):
            self.destroy()
    
    def _poison_nearby_mushrooms(self):
        """Poison mushrooms that scorpion touches"""
        if not hasattr(self.scene, 'game_objects'):
            return
            
        mushrooms = [obj for obj in self.scene.game_objects 
                    if isinstance(obj, Mushroom) and not obj.is_destroyed]
        
        for mushroom in mushrooms:
            distance = self.transform.position.distance_to(mushroom.transform.position)
            if distance < 12:
                mushroom.poison()
    
    def hit(self):
        """Scorpion is hit by dart"""
        if hasattr(self.scene, 'engine'):
            self.scene.engine.score += self.points
        self.destroy()


class CentipedeGame(GameEngine):
    """Main Centipede game"""
    
    def __init__(self):
        super().__init__("Centipede - Classic Arcade Game", (800, 600), 60)
        self.score = 0
        self.lives = 3
        self.level = 1
        self.centipede_segments = []
        self.current_centipede_length = 12
        
        # Spawn timers
        self.flea_spawn_timer = 0.0
        self.spider_spawn_timer = 0.0
        self.scorpion_spawn_timer = 0.0
        
        # Spawn rates (seconds)
        self.flea_spawn_rate = 8.0
        self.spider_spawn_rate = 15.0
        self.scorpion_spawn_rate = 25.0
        
        # Initialize sound system
        self.sound_generator = SoundGenerator()
        self.create_centipede_sounds()
    
    def create_centipede_sounds(self):
        """Create Centipede-style sound effects"""
        try:
            from engine.audio.sound_generator import Sound
            
            # Shooting sound
            shoot_sound = Sound("shoot")
            shoot_sound.generate_tone(800, 0.1, 'square', 0.3)
            self.sound_generator.register_sound(shoot_sound)
            
            # Hit sound
            hit_sound = Sound("hit")
            hit_sound.generate_tone(400, 0.15, 'square', 0.4)
            self.sound_generator.register_sound(hit_sound)
            
            # Death sound
            death_sound = Sound("death")
            death_sound.generate_sweep(600, 100, 0.8, 'square', 0.5)
            self.sound_generator.register_sound(death_sound)
            
            # Level complete sound
            level_complete_sound = Sound("level_complete")
            level_complete_sound.generate_sweep(200, 800, 1.5, 'square', 0.4)
            self.sound_generator.register_sound(level_complete_sound)
            
            print("Sound effects loaded successfully!")
            
        except Exception as e:
            print(f"Error loading sounds: {e}")
            self.sound_generator = None
    
    def initialize(self):
        """Initialize the game"""
        self.setup_game()
        
        print("Centipede - Classic Arcade Game")
        print("Controls:")
        print("  WASD or Arrow Keys - Move Bug Blaster")
        print("  Space or Ctrl - Shoot darts")
        print("  ESC - Quit")
        print("")
        print("Enemies:")
        print("  Centipede Head: 100 points")
        print("  Centipede Body: 10 points")
        print("  Flea: 200 points (2 hits)")
        print("  Spider: 300-900 points")
        print("  Scorpion: 1000 points")
        print("  Mushroom: 1 point (4 hits to destroy)")
        print("")
        print("Watch out for poison mushrooms!")
    
    def setup_game(self):
        """Set up game objects"""
        # Clear existing objects
        if self.current_scene:
            self.current_scene.game_objects.clear()
        
        # Create player
        self.player = BugBlaster()
        self.current_scene.add_object(self.player)
        
        # Create initial mushroom field
        self.create_mushroom_field()
        
        # Create initial centipede
        self.spawn_centipede()
        
        # Give scene access to engine
        self.current_scene.engine = self
    
    def create_mushroom_field(self):
        """Create random mushroom field"""
        # Create mushrooms in a grid pattern with some randomness
        for y in range(100, 380, 20):
            for x in range(50, 750, 20):
                if random.random() < 0.15:  # 15% chance for mushroom
                    mushroom = Mushroom(x, y)
                    self.current_scene.add_object(mushroom)
    
    def spawn_centipede(self):
        """Spawn a new centipede"""
        self.centipede_segments = []
        
        # Start position
        start_x = 50 if random.choice([True, False]) else 750
        start_y = 50
        
        # Create segments
        for i in range(self.current_centipede_length):
            is_head = (i == 0)
            segment = CentipedeSegment(is_head)
            segment.transform.position = Vector2(start_x + i * 16, start_y)
            
            # Set direction based on starting side
            if start_x > 400:
                segment.direction = Vector2(-1, 0)
            
            self.centipede_segments.append(segment)
            self.current_scene.add_object(segment)
    
    def _split_centipede_at_segment(self, hit_segment):
        """Split centipede when a middle segment is hit"""
        if hit_segment not in self.centipede_segments:
            return
        
        hit_index = self.centipede_segments.index(hit_segment)
        
        # Remove the hit segment
        self.centipede_segments.remove(hit_segment)
        
        # Split into two groups
        if hit_index > 0:
            # Segments before the hit become independent
            for i in range(hit_index):
                if i < len(self.centipede_segments):
                    segment = self.centipede_segments[i]
                    if i == hit_index - 1:
                        # Last segment in first group becomes head
                        segment.is_head = True
                        sprite = Sprite(color='#FFFF00', size=Vector2(12, 12))
                        segment.remove_component(Sprite)
                        segment.add_component(sprite)
        
        # Segments after the hit continue as normal
        # (The first remaining segment is already a head or becomes one)
        if self.centipede_segments:
            # Make sure first remaining segment is a head
            first_remaining = self.centipede_segments[0]
            if not first_remaining.is_head:
                first_remaining.is_head = True
                sprite = Sprite(color='#FFFF00', size=Vector2(12, 12))
                first_remaining.remove_component(Sprite)
                first_remaining.add_component(sprite)
    
    def update(self, delta_time: float):
        """Game update logic"""
        super().update(delta_time)
        
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        
        # Update spawn timers
        self.flea_spawn_timer += delta_time
        self.spider_spawn_timer += delta_time
        self.scorpion_spawn_timer += delta_time
        
        # Spawn enemies
        self._spawn_enemies()
        
        # Check win condition (all centipede segments destroyed)
        remaining_segments = [obj for obj in self.current_scene.game_objects 
                             if isinstance(obj, CentipedeSegment) and not obj.is_destroyed]
        
        if not remaining_segments:
            self._next_level()
        
        # Check player collision with enemies
        self._check_player_collisions()
        
        # Check for extra life
        if self.score >= 12000 and not hasattr(self, 'extra_life_awarded'):
            self.lives += 1
            self.extra_life_awarded = True
            print("Extra life awarded!")
    
    def _spawn_enemies(self):
        """Spawn various enemies based on timers"""
        # Spawn flea
        if self.flea_spawn_timer >= self.flea_spawn_rate:
            # Only spawn if few mushrooms in player area
            player_area_mushrooms = [obj for obj in self.current_scene.game_objects 
                                   if isinstance(obj, Mushroom) and not obj.is_destroyed 
                                   and obj.transform.position.y > 400]
            
            if len(player_area_mushrooms) < 3:
                flea = Flea()
                self.current_scene.add_object(flea)
            
            self.flea_spawn_timer = 0.0
        
        # Spawn spider
        if self.spider_spawn_timer >= self.spider_spawn_rate:
            spider = Spider()
            self.current_scene.add_object(spider)
            self.spider_spawn_timer = 0.0
        
        # Spawn scorpion
        if self.scorpion_spawn_timer >= self.scorpion_spawn_rate:
            scorpion = Scorpion()
            self.current_scene.add_object(scorpion)
            self.scorpion_spawn_timer = 0.0
    
    def _check_player_collisions(self):
        """Check if player collides with any enemies"""
        if not self.player or self.player.is_destroyed:
            return
        
        player_pos = self.player.transform.position
        
        # Check all enemies
        enemies = [obj for obj in self.current_scene.game_objects 
                  if isinstance(obj, (CentipedeSegment, Flea, Spider, Scorpion)) 
                  and not obj.is_destroyed]
        
        for enemy in enemies:
            distance = player_pos.distance_to(enemy.transform.position)
            if distance < 12:
                self._player_death()
                return
    
    def _player_death(self):
        """Handle player death"""
        self.lives -= 1
        
        if self.sound_generator:
            self.sound_generator.play_sound("death")
        
        print(f"Player destroyed! Lives remaining: {self.lives}")
        
        if self.lives <= 0:
            self._game_over()
        else:
            # Regenerate damaged mushrooms
            self._regenerate_mushrooms()
            
            # Reset player position
            self.player.transform.position = Vector2(400, 550)
    
    def _regenerate_mushrooms(self):
        """Regenerate mushrooms when player dies"""
        mushrooms = [obj for obj in self.current_scene.game_objects 
                    if isinstance(obj, Mushroom) and not obj.is_destroyed]
        
        regenerated_count = 0
        for mushroom in mushrooms:
            if mushroom.hits > 0 or mushroom.is_poisoned:
                mushroom.heal()
                regenerated_count += 1
        
        # Award points for regenerated mushrooms
        self.score += regenerated_count * 5
        if regenerated_count > 0:
            print(f"Regenerated {regenerated_count} mushrooms (+{regenerated_count * 5} points)")
    
    def _next_level(self):
        """Advance to next level"""
        self.level += 1
        
        if self.sound_generator:
            self.sound_generator.play_sound("level_complete")
        
        print(f"Level {self.level} complete!")
        
        # Next centipede is shorter but has more heads
        self.current_centipede_length = max(1, self.current_centipede_length - 1)
        
        # Spawn new centipede
        self.spawn_centipede()
        
        # Increase difficulty
        self.flea_spawn_rate = max(5.0, self.flea_spawn_rate - 0.5)
        self.spider_spawn_rate = max(10.0, self.spider_spawn_rate - 1.0)
        self.scorpion_spawn_rate = max(15.0, self.scorpion_spawn_rate - 2.0)
    
    def _game_over(self):
        """Handle game over"""
        print(f"Game Over! Final Score: {self.score}")
        print(f"Level Reached: {self.level}")
        # Could add restart functionality here
    
    def render(self):
        """Custom rendering for UI"""
        super().render()
        
        # Draw score
        self.renderer.draw_text(
            Vector2(100, 30), 
            f"SCORE: {self.score:06d}", 
            '#FFFFFF', 
            16
        )
        
        # Draw lives
        self.renderer.draw_text(
            Vector2(300, 30), 
            f"LIVES: {self.lives}", 
            '#FFFFFF', 
            16
        )
        
        # Draw level
        self.renderer.draw_text(
            Vector2(500, 30), 
            f"LEVEL: {self.level}", 
            '#FFFFFF', 
            16
        )
        
        # Draw player area divider line
        self.renderer.draw_line(
            Vector2(0, 400), 
            Vector2(800, 400), 
            '#FFFFFF', 
            2
        )
        
        if self.lives <= 0:
            self.renderer.draw_text(
                Vector2(400, 300), 
                "GAME OVER", 
                '#FF0000', 
                32, 
                'center'
            )
            self.renderer.draw_text(
                Vector2(400, 340), 
                f"FINAL SCORE: {self.score:06d}", 
                '#FFFFFF', 
                20, 
                'center'
            )


if __name__ == "__main__":
    game = CentipedeGame()
    game.run()
