"""
2D Horizontally Scrolling Space Shooter
Built using the Pure Python 2D Game Engine
"""
import math
import random
from typing import List
from engine import GameEngine, GameObject, Vector2, Sprite, SoundGenerator


class ScrollingBackground(GameObject):
    """Scrolling starfield background"""

    def __init__(self):
        super().__init__("Background")
        self.scroll_speed = 50.0
        self.stars = []
        self.generate_stars()

    def generate_stars(self):
        """Generate random stars for the background"""
        for _ in range(100):
            star = {
                'pos': Vector2(random.randint(0, 1600), random.randint(0,
                                                                       600)),
                'size': random.uniform(1, 3),
                'brightness': random.uniform(0.3, 1.0)
            }
            self.stars.append(star)

    def update(self, delta_time: float):
        super().update(delta_time)

        # Scroll stars left
        for star in self.stars:
            star['pos'].x -= self.scroll_speed * delta_time

            # Wrap around when star goes off screen
            if star['pos'].x < -10:
                star['pos'].x = 810
                star['pos'].y = random.randint(0, 600)

    def render(self, renderer):
        """Render the starfield"""
        for star in self.stars:
            # Vary star color based on brightness
            brightness = int(255 * star['brightness'])
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
            renderer.draw_circle(star['pos'], star['size'], color)


class Player(GameObject):
    """Player spacecraft"""

    # Power-up durations, shared by activate_power_up() and the HUD readout
    SPEED_BOOST_DURATION = 8.0
    RAPID_FIRE_DURATION = 10.0
    SHIELD_DURATION = 15.0

    def __init__(self):
        super().__init__("Player")
        self.speed = 300.0
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0.0
        self.shoot_delay = 0.15
        self.score = 0

        # Power-up effects
        self.rapid_fire_timer = 0.0
        self.speed_boost_timer = 0.0
        self.shield_timer = 0.0
        self.has_shield = False

        # Player ship sprite (futuristic fighter)
        sprite = Sprite(color='#CCCCCC', size=Vector2(40, 30))
        self.add_component(sprite)

        # Start position (left side of screen)
        self.transform.position = Vector2(100, 300)

    def update(self, delta_time: float):
        super().update(delta_time)

        self.shoot_cooldown -= delta_time

        # Update power-up timers
        if self.rapid_fire_timer > 0:
            self.rapid_fire_timer -= delta_time
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= delta_time
        else:
            self.speed = 300.0  # Reset to normal speed
        if self.shield_timer > 0:
            self.shield_timer -= delta_time
            self.has_shield = True
        else:
            self.has_shield = False

        if not hasattr(self.scene, 'engine'):
            return

        input_manager = self.scene.engine.input_manager

        # Movement (vertical only for side-scroller)
        movement = Vector2.zero()
        if input_manager.is_key_pressed('up') or input_manager.is_key_pressed(
                'w'):
            movement.y = -1
        if input_manager.is_key_pressed(
                'down') or input_manager.is_key_pressed('s'):
            movement.y = 1

        # Optional horizontal movement (limited)
        if input_manager.is_key_pressed(
                'left') or input_manager.is_key_pressed('a'):
            movement.x = -0.5
        if input_manager.is_key_pressed(
                'right') or input_manager.is_key_pressed('d'):
            movement.x = 0.5

        # Apply movement
        if movement.magnitude > 0:
            new_pos = self.transform.position + movement.normalize(
            ) * self.speed * delta_time

            # Keep player on screen (full screen movement)
            new_pos.x = max(20, min(780,
                                    new_pos.x))  # Full horizontal movement
            new_pos.y = max(20, min(580, new_pos.y))

            self.transform.position = new_pos

        # Shooting
        if (input_manager.is_key_pressed('space')
                or input_manager.is_key_pressed('ctrl')
            ) and self.shoot_cooldown <= 0:
            self._shoot()
            # Apply rapid fire if active
            if self.rapid_fire_timer > 0:
                self.shoot_cooldown = self.shoot_delay * 0.3  # 3x faster
            else:
                self.shoot_cooldown = self.shoot_delay

    def _shoot(self):
        """Fire a bullet"""
        if hasattr(self.scene, 'engine'):
            bullet = PlayerBullet()
            bullet.transform.position = Vector2(self.transform.position.x + 25,
                                                self.transform.position.y)
            bullet.engine = self.scene.engine
            self.scene.add_object(bullet)

            # Play shooting sound
            if hasattr(self.scene.engine, 'sound_generator'):
                self.scene.engine.sound_generator.play_sound("player_shoot")

    def take_damage(self, damage: int):
        """Take damage"""
        if self.has_shield:
            return  # Shield protects from damage

        self.health -= damage
        self.health = max(0, self.health)

        # Flash effect when hit
        sprite = self.get_component(Sprite)
        if sprite:
            sprite.color = '#FF0000'  # Red flash

    def heal_flash(self):
        """Reset color after damage flash"""
        sprite = self.get_component(Sprite)
        if sprite:
            if self.has_shield:
                sprite.color = '#00FFFF'  # Cyan for shield
            else:
                sprite.color = '#CCCCCC'

    def activate_power_up(self, power_type: str):
        """Activate a power-up effect"""
        if power_type == "health":
            self.health = min(self.max_health, self.health + 50)
        elif power_type == "speed":
            self.speed = 450.0
            self.speed_boost_timer = self.SPEED_BOOST_DURATION
        elif power_type == "weapon":
            self.rapid_fire_timer = self.RAPID_FIRE_DURATION
        elif power_type == "shield":
            self.shield_timer = self.SHIELD_DURATION
            self.has_shield = True

    def render(self, renderer):
        """Custom render for player ship"""
        pos = self.transform.position

        # Draw futuristic fighter ship
        # Main body
        renderer.draw_rectangle(pos, Vector2(35, 20), '#CCCCCC')

        # Cockpit
        renderer.draw_rectangle(Vector2(pos.x + 10, pos.y), Vector2(15, 12),
                                '#4444AA')

        # Wings
        renderer.draw_rectangle(Vector2(pos.x - 5, pos.y - 8), Vector2(20, 6),
                                '#AAAAAA')
        renderer.draw_rectangle(Vector2(pos.x - 5, pos.y + 8), Vector2(20, 6),
                                '#AAAAAA')

        # Engine glow
        renderer.draw_circle(Vector2(pos.x - 20, pos.y), 4, '#00AAFF')

        # Shield effect
        if self.has_shield:
            renderer.draw_circle(pos, 35, color='', outline='#00FFFF', width=2)


class PlayerBullet(GameObject):
    """Player bullet projectile"""

    def __init__(self):
        super().__init__("PlayerBullet")
        self.velocity = Vector2(600, 0)  # Fast rightward movement
        self.damage = 25

        # Blue energy bullet
        sprite = Sprite(color='#00AAFF', size=Vector2(12, 4))
        self.add_component(sprite)

    def update(self, delta_time: float):
        super().update(delta_time)

        # Move bullet
        self.transform.position += self.velocity * delta_time

        # Remove if off screen
        if self.transform.position.x > 850:
            self.destroy()

        # Check collisions with enemies
        if hasattr(self.scene, 'engine'):
            self._check_enemy_collisions()

    def _check_enemy_collisions(self):
        """Check bullet collisions with enemies"""
        bullet_pos = self.transform.position

        enemies = [
            obj for obj in self.scene.game_objects
            if isinstance(obj, Enemy) and not obj.is_destroyed
        ]

        for enemy in enemies:
            distance = bullet_pos.distance_to(enemy.transform.position)
            if distance < 20:
                enemy.hit(self.damage)
                self.destroy()
                return

    def render(self, renderer):
        """Custom bullet render"""
        pos = self.transform.position

        # Draw glowing energy bullet
        renderer.draw_rectangle(pos, Vector2(12, 3), '#00AAFF')
        renderer.draw_rectangle(pos, Vector2(8, 2), '#FFFFFF')  # Bright core


class Enemy(GameObject):
    """Enemy spacecraft"""

    def __init__(self, enemy_type="basic", wave=1):
        super().__init__("Enemy")
        self.enemy_type = enemy_type
        self.wave = wave
        
        # Base stats that scale with wave
        wave_multiplier = 1.0 + (wave - 1) * 0.3  # 30% increase per wave
        speed_multiplier = 1.0 + (wave - 1) * 0.2  # 20% speed increase per wave
        
        self.speed = 80.0 * speed_multiplier
        self.health = int(50 * wave_multiplier)
        self.max_health = self.health
        self.points = int(100 * wave_multiplier)
        self.shoot_timer = 0.0
        self.shoot_interval = max(0.5, 2.0 - (wave - 1) * 0.15)  # Faster shooting each wave
        self.movement_pattern = "straight"
        self.pattern_timer = 0.0
        
        # Shooting patterns based on wave
        if wave >= 5:
            self.shooting_pattern = random.choice(["single", "burst", "spread"])
        elif wave >= 3:
            self.shooting_pattern = random.choice(["single", "burst"])
        else:
            self.shooting_pattern = "single"

        # Different enemy types
        if enemy_type == "fast":
            self.speed = 120.0 * speed_multiplier
            self.health = int(25 * wave_multiplier)
            self.points = int(150 * wave_multiplier)
            self.shoot_interval = max(0.3, 1.5 - (wave - 1) * 0.1)
            sprite = Sprite(color='#FF4444', size=Vector2(30, 20))
        elif enemy_type == "heavy":
            self.speed = 50.0 * speed_multiplier
            self.health = int(100 * wave_multiplier)
            self.points = int(200 * wave_multiplier)
            self.shoot_interval = max(0.4, 1.0 - (wave - 1) * 0.08)
            sprite = Sprite(color='#444444', size=Vector2(40, 30))
        else:  # basic
            sprite = Sprite(color='#FF8844', size=Vector2(35, 25))

        self.add_component(sprite)

        # Start at random position on right side
        self.transform.position = Vector2(850, random.randint(50, 550))

        # Random movement pattern
        self.movement_pattern = random.choice(["straight", "sine", "zigzag"])
        self.initial_y = self.transform.position.y

    def update(self, delta_time: float):
        super().update(delta_time)

        self.shoot_timer += delta_time
        self.pattern_timer += delta_time

        # Movement patterns
        if self.movement_pattern == "straight":
            self.transform.position.x -= self.speed * delta_time
        elif self.movement_pattern == "sine":
            self.transform.position.x -= self.speed * delta_time
            offset = math.sin(self.pattern_timer * 2) * 50
            self.transform.position.y = self.initial_y + offset
        elif self.movement_pattern == "zigzag":
            self.transform.position.x -= self.speed * delta_time
            if int(self.pattern_timer * 2) % 2:
                self.transform.position.y += 30 * delta_time
            else:
                self.transform.position.y -= 30 * delta_time

        # Keep enemy on screen vertically
        self.transform.position.y = max(30, min(570,
                                                self.transform.position.y))

        # Shooting
        if self.shoot_timer >= self.shoot_interval:
            self._shoot()
            self.shoot_timer = 0.0

        # Remove if off screen
        if self.transform.position.x < -50:
            self.destroy()

        # Check collision with player
        if hasattr(self.scene, 'engine'):
            self._check_player_collision()

    def _shoot(self):
        """Fire at player with different patterns"""
        if hasattr(self.scene, 'engine'):
            player = self.scene.find_object("Player")
            if player:
                if self.shooting_pattern == "burst":
                    self._shoot_burst(player)
                elif self.shooting_pattern == "spread":
                    self._shoot_spread(player)
                else:
                    self._shoot_single(player)

                # Play enemy shoot sound
                if hasattr(self.scene.engine, 'sound_generator'):
                    self.scene.engine.sound_generator.play_sound("enemy_shoot")
    
    def _shoot_single(self, player):
        """Fire single bullet at player"""
        bullet = EnemyBullet()
        bullet.transform.position = Vector2(
            self.transform.position.x - 20, self.transform.position.y)

        # Aim at player
        direction = (player.transform.position -
                     bullet.transform.position).normalize()
        bullet.velocity = direction * 300

        bullet.engine = self.scene.engine
        self.scene.add_object(bullet)
    
    def _shoot_burst(self, player):
        """Fire 3-bullet burst at player"""
        for i in range(3):
            bullet = EnemyBullet()
            bullet.transform.position = Vector2(
                self.transform.position.x - 20, self.transform.position.y)

            # Aim at player with slight variation
            direction = (player.transform.position -
                         bullet.transform.position).normalize()
            
            # Add slight spread to burst
            angle_offset = (i - 1) * 0.1  # -0.1, 0, 0.1 radians
            rotated_direction = Vector2(
                direction.x * math.cos(angle_offset) - direction.y * math.sin(angle_offset),
                direction.x * math.sin(angle_offset) + direction.y * math.cos(angle_offset)
            )
            
            bullet.velocity = rotated_direction * 300
            bullet.engine = self.scene.engine
            self.scene.add_object(bullet)
    
    def _shoot_spread(self, player):
        """Fire spread shot (5 bullets in a fan)"""
        for i in range(5):
            bullet = EnemyBullet()
            bullet.transform.position = Vector2(
                self.transform.position.x - 20, self.transform.position.y)

            # Create spread pattern
            base_direction = (player.transform.position -
                            bullet.transform.position).normalize()
            
            # Spread angles: -0.4, -0.2, 0, 0.2, 0.4 radians
            angle_offset = (i - 2) * 0.2
            rotated_direction = Vector2(
                base_direction.x * math.cos(angle_offset) - base_direction.y * math.sin(angle_offset),
                base_direction.x * math.sin(angle_offset) + base_direction.y * math.cos(angle_offset)
            )
            
            bullet.velocity = rotated_direction * 280
            bullet.engine = self.scene.engine
            self.scene.add_object(bullet)

    def _check_player_collision(self):
        """Check collision with player"""
        player = self.scene.find_object("Player")
        if player and not player.is_destroyed:
            distance = self.transform.position.distance_to(
                player.transform.position)
            if distance < 30:
                player.take_damage(20)
                self.destroy()

                # Schedule healing flash
                if hasattr(self.scene.engine, 'current_scene'):

                    def heal_flash():
                        if not player.is_destroyed:
                            player.heal_flash()

                    # Simple timer for flash effect
                    flash_timer = FlashTimer(heal_flash, 0.1)
                    self.scene.add_object(flash_timer)

    def hit(self, damage: int):
        """Enemy is hit by player bullet"""
        self.health -= damage

        if self.health <= 0:
            # Award points to player
            player = self.scene.find_object("Player")
            if player:
                player.score += self.points

            # Play explosion sound
            if hasattr(self.scene, 'engine') and hasattr(
                    self.scene.engine, 'sound_generator'):
                self.scene.engine.sound_generator.play_sound("explosion")

            self.destroy()

    def render(self, renderer):
        """Custom render for enemy ship"""
        pos = self.transform.position

        if self.enemy_type == "fast":
            # Fast interceptor
            renderer.draw_rectangle(pos, Vector2(25, 15), '#FF4444')
            renderer.draw_circle(Vector2(pos.x - 10, pos.y), 3, '#FFAA00')
        elif self.enemy_type == "heavy":
            # Heavy bomber
            renderer.draw_rectangle(pos, Vector2(40, 25), '#444444')
            renderer.draw_rectangle(Vector2(pos.x, pos.y - 10), Vector2(20, 8),
                                    '#666666')
            renderer.draw_rectangle(Vector2(pos.x, pos.y + 10), Vector2(20, 8),
                                    '#666666')
        else:
            # Basic fighter
            renderer.draw_rectangle(pos, Vector2(30, 20), '#FF8844')
            renderer.draw_circle(Vector2(pos.x - 12, pos.y), 4, '#FF0000')


class EnemyBullet(GameObject):
    """Enemy bullet projectile"""

    def __init__(self):
        super().__init__("EnemyBullet")
        self.velocity = Vector2(-300, 0)
        self.damage = 15

        # Red enemy bullet
        sprite = Sprite(color='#FF0000', size=Vector2(8, 3))
        self.add_component(sprite)

    def update(self, delta_time: float):
        super().update(delta_time)

        # Move bullet
        self.transform.position += self.velocity * delta_time

        # Remove if off screen
        if (self.transform.position.x < -20 or self.transform.position.x > 820
                or self.transform.position.y < -20
                or self.transform.position.y > 620):
            self.destroy()

        # Check collision with player
        if hasattr(self.scene, 'engine'):
            self._check_player_collision()

    def _check_player_collision(self):
        """Check bullet collision with player"""
        player = self.scene.find_object("Player")
        if player and not player.is_destroyed:
            distance = self.transform.position.distance_to(
                player.transform.position)
            if distance < 15:
                player.take_damage(self.damage)
                self.destroy()


class FlashTimer(GameObject):
    """Simple timer for visual effects"""

    def __init__(self, callback, duration):
        super().__init__("FlashTimer")
        self.callback = callback
        self.duration = duration
        self.timer = 0.0

    def update(self, delta_time: float):
        super().update(delta_time)

        self.timer += delta_time
        if self.timer >= self.duration:
            if self.callback:
                self.callback()
            self.destroy()


class PowerUp(GameObject):
    """Power-up collectibles"""

    def __init__(self, power_type="health"):
        super().__init__("PowerUp")
        self.power_type = power_type
        self.speed = 60.0
        self.collected = False
        self.rotation_speed = 2.0

        # Different power-up types with distinct colors and sizes
        if power_type == "health":
            sprite = Sprite(color='#00FF00', size=Vector2(20,
                                                          20))  # Green health
        elif power_type == "speed":
            sprite = Sprite(color='#FFFF00', size=Vector2(18,
                                                          18))  # Yellow speed
        elif power_type == "weapon":
            sprite = Sprite(color='#FF00FF',
                            size=Vector2(16, 16))  # Magenta rapid fire
        else:  # shield
            sprite = Sprite(color='#00FFFF', size=Vector2(22,
                                                          22))  # Cyan shield

        self.add_component(sprite)

        # Start at random position on right side
        self.transform.position = Vector2(850, random.randint(100, 500))

    def update(self, delta_time: float):
        super().update(delta_time)

        # Move left and rotate for visual effect
        self.transform.position.x -= self.speed * delta_time
        self.transform.rotate(self.rotation_speed * delta_time)

        # Remove if off screen
        if self.transform.position.x < -20:
            self.destroy()

        # Check collision with player
        if hasattr(self.scene, 'engine') and not self.collected:
            self._check_player_collision()

    def _check_player_collision(self):
        """Check if player collects power-up"""
        player = self.scene.find_object("Player")
        if player and not player.is_destroyed:
            distance = self.transform.position.distance_to(
                player.transform.position)
            if distance < 20:
                self._apply_power_up(player)
                self.collected = True
                self.destroy()

    def _apply_power_up(self, player):
        """Apply power-up effect to player"""
        player.activate_power_up(self.power_type)

        if self.power_type == "health":
            print("Health restored!")
        elif self.power_type == "speed":
            print("Speed boost activated!")
        elif self.power_type == "weapon":
            print("Rapid fire activated!")
        else:  # shield
            print("Shield activated!")


class SpaceShooterGame(GameEngine):
    """Main space shooter game"""

    def __init__(self):
        super().__init__("2D Space Shooter", (800, 600), 60)
        self.player = None
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_rate = 2.0
        self.powerup_spawn_timer = 0.0
        self.powerup_spawn_rate = 10.0
        self.wave = 1
        self.enemies_spawned = 0
        self.enemies_per_wave = 10
        self.game_over = False

        # Initialize sound system
        self.sound_generator = SoundGenerator()
        self.create_space_sounds()

    def create_space_sounds(self):
        """Create space shooter sound effects"""
        try:
            from engine.audio.sound_generator import Sound

            # Player shooting sound - high pitched laser
            player_shoot = Sound("player_shoot")
            player_shoot.generate_sweep(800, 400, 0.08, 'square', 0.4)
            self.sound_generator.register_sound(player_shoot)

            # Enemy shooting sound - lower, slower, grittier descending laser
            enemy_shoot = Sound("enemy_shoot")
            enemy_shoot.generate_sweep(350, 150, 0.14, 'sawtooth', 0.35)
            self.sound_generator.register_sound(enemy_shoot)

            # Explosion sound for destroyed ships
            explosion = Sound("explosion")
            explosion.generate_explosion(0.4, 0.5)
            self.sound_generator.register_sound(explosion)

            print("Sound effects loaded successfully!")

        except Exception as e:
            print(f"Error loading sounds: {e}")
            self.sound_generator = None

    def initialize(self):
        """Initialize the game"""
        self.setup_game()

        print("2D Space Shooter")
        print("Controls:")
        print("  W/S or Up/Down - Move vertically")
        print("  A/D or Left/Right - Move horizontally (limited)")
        print("  Space or Ctrl - Shoot")
        print("  ESC - Quit")
        print("")
        print("Defeat enemies and collect power-ups!")
        print(
            "Green = Health, Yellow = Speed, Purple = Rapid Fire, Cyan = Shield"
        )

    def setup_game(self):
        """Set up game objects"""
        # Clear existing objects
        if self.current_scene:
            self.current_scene.game_objects.clear()

        # Create scrolling background
        background = ScrollingBackground()
        self.current_scene.add_object(background)

        # Create player
        self.player = Player()
        self.current_scene.add_object(self.player)

        # Give scene access to engine
        self.current_scene.engine = self

    def update(self, delta_time: float):
        """Game update logic"""
        super().update(delta_time)

        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()

        if self.game_over:
            # Game is over, only allow restart
            if self.input_manager.is_key_just_pressed('r'):
                self._restart_game()
            return

        # Check player death
        if self.player and self.player.health <= 0:
            self.game_over = True
            print(f"Game Over! Final Score: {self.player.score}")
            print("Press 'R' to restart")
            return

        # Update spawn timers
        self.enemy_spawn_timer += delta_time
        self.powerup_spawn_timer += delta_time

        # Spawn enemies
        if (self.enemy_spawn_timer >= self.enemy_spawn_rate
                and self.enemies_spawned < self.enemies_per_wave):
            self._spawn_enemy()
            self.enemy_spawn_timer = 0.0
            self.enemies_spawned += 1

        # Spawn power-ups (less frequent in later waves)
        current_powerup_rate = self.powerup_spawn_rate + (self.wave - 1) * 2.0  # Longer intervals each wave
        if self.powerup_spawn_timer >= current_powerup_rate:
            self._spawn_powerup()
            self.powerup_spawn_timer = 0.0

        # Check wave completion
        enemies = [
            obj for obj in self.current_scene.game_objects
            if isinstance(obj, Enemy) and not obj.is_destroyed
        ]

        if self.enemies_spawned >= self.enemies_per_wave and len(enemies) == 0:
            self._next_wave()

    def _spawn_enemy(self):
        """Spawn a new enemy"""
        # Choose enemy type based on wave
        if self.wave >= 3:
            enemy_type = random.choice(["basic", "fast", "heavy"])
        elif self.wave >= 2:
            enemy_type = random.choice(["basic", "fast"])
        else:
            enemy_type = "basic"

        enemy = Enemy(enemy_type, self.wave)
        self.current_scene.add_object(enemy)

    def _spawn_powerup(self):
        """Spawn a power-up with weighted probabilities"""
        # Make health power-ups much more rare (5% chance vs 25% for others)
        rand_val = random.random()
        if rand_val < 0.05:  # 5% chance for health
            powerup_type = "health"
        elif rand_val < 0.35:  # 30% chance for speed
            powerup_type = "speed"
        elif rand_val < 0.65:  # 30% chance for weapon
            powerup_type = "weapon"
        else:  # 35% chance for shield
            powerup_type = "shield"
            
        powerup = PowerUp(powerup_type)
        self.current_scene.add_object(powerup)

    def _next_wave(self):
        """Start next wave"""
        self.wave += 1
        self.enemies_spawned = 0
        self.enemies_per_wave = min(15, 8 + self.wave * 2)
        self.enemy_spawn_rate = max(0.8, 2.0 - self.wave * 0.1)

        print(f"Wave {self.wave} - {self.enemies_per_wave} enemies incoming!")

        # Bonus points for wave completion
        if self.player:
            self.player.score += self.wave * 500

    def _restart_game(self):
        """Restart the game"""
        self.game_over = False
        self.wave = 1
        self.enemies_spawned = 0
        self.enemies_per_wave = 10
        self.enemy_spawn_rate = 2.0
        self.enemy_spawn_timer = 0.0
        self.powerup_spawn_timer = 0.0

        # Clear scene and recreate
        self.setup_game()
        print("Game restarted!")

    def render(self):
        """Custom rendering for UI"""
        super().render()

        if not self.player:
            return

        # Draw UI
        self.renderer.draw_text(Vector2(80,
                                        30), f"Score: {self.player.score:06d}",
                                '#FFFFFF', 16)

        self.renderer.draw_text(Vector2(200, 30), f"Wave: {self.wave}",
                                '#FFFFFF', 16)

        # Health bar
        health_percent = self.player.health / self.player.max_health
        bar_width = 100
        bar_height = 8

        # Background
        self.renderer.draw_rectangle(Vector2(650, 30),
                                     Vector2(bar_width, bar_height), '#444444')

        # Health bar
        health_width = bar_width * health_percent
        health_color = '#00FF00' if health_percent > 0.5 else '#FFFF00' if health_percent > 0.25 else '#FF0000'

        if health_width > 0:
            self.renderer.draw_rectangle(Vector2(650, 30),
                                         Vector2(health_width, bar_height),
                                         health_color)

        self.renderer.draw_text(Vector2(760, 30), f"Health", '#FFFFFF', 14)

        # Active power-up indicators
        self._draw_powerup_status()

        if self.game_over:
            self.renderer.draw_text(Vector2(400, 250), "GAME OVER", '#FF0000',
                                    36, 'center')
            self.renderer.draw_text(Vector2(400, 300),
                                    f"Final Score: {self.player.score:06d}",
                                    '#FFFFFF', 20, 'center')
            self.renderer.draw_text(Vector2(400, 350),
                                    f"Waves Completed: {self.wave - 1}",
                                    '#FFFFFF', 16, 'center')
            self.renderer.draw_text(Vector2(400, 400), "Press 'R' to restart",
                                    '#FFFF00', 18, 'center')

    def _draw_powerup_status(self):
        """Draw a status readout for each currently active power-up effect"""
        active_effects = []
        if self.player.speed_boost_timer > 0:
            active_effects.append(
                ("SPEED BOOST", self.player.speed_boost_timer,
                 self.player.SPEED_BOOST_DURATION, '#FFFF00'))
        if self.player.rapid_fire_timer > 0:
            active_effects.append(
                ("RAPID FIRE", self.player.rapid_fire_timer,
                 self.player.RAPID_FIRE_DURATION, '#FF00FF'))
        if self.player.shield_timer > 0:
            active_effects.append(
                ("SHIELD", self.player.shield_timer,
                 self.player.SHIELD_DURATION, '#00FFFF'))

        if not active_effects:
            return

        x = 20
        bar_width = 100
        bar_height = 6

        for i, (label, remaining, duration, color) in enumerate(active_effects):
            y = 55 + i * 20

            self.renderer.draw_text(Vector2(x, y), f"{label}: {remaining:.1f}s",
                                    color, 12, 'w')

            bar_y = y + 10
            self.renderer.draw_rectangle(Vector2(x + bar_width / 2, bar_y),
                                         Vector2(bar_width, bar_height), '#444444')

            filled_width = bar_width * max(0.0, min(1.0, remaining / duration))
            if filled_width > 0:
                self.renderer.draw_rectangle(Vector2(x + filled_width / 2, bar_y),
                                             Vector2(filled_width, bar_height), color)


if __name__ == "__main__":
    game = SpaceShooterGame()
    game.run()
