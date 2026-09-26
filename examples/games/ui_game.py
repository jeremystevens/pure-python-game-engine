
"""
Complete game example with UI, multiple scenes, and particle effects
"""
import math
import random
from engine import GameEngine, GameObject, Vector2, Transform, Sprite, Scene


class ParticleSystem(GameObject):
    """Simple particle system for visual effects"""
    
    def __init__(self, name: str = "ParticleSystem"):
        super().__init__(name)
        self.particles = []
        self.max_particles = 50
        self.emit_rate = 5.0
        self.emit_timer = 0.0
        self.gravity = Vector2(0, 98)  # Gravity effect
        
    def emit_particle(self, position: Vector2, velocity: Vector2, color: str = '#FFD700', life: float = 2.0):
        """Emit a new particle"""
        if len(self.particles) < self.max_particles:
            particle = {
                'position': position.copy(),
                'velocity': velocity.copy(),
                'color': color,
                'life': life,
                'max_life': life,
                'size': random.uniform(2, 6)
            }
            self.particles.append(particle)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Update existing particles
        for particle in self.particles[:]:
            particle['position'] += particle['velocity'] * delta_time
            particle['velocity'] += self.gravity * delta_time
            particle['life'] -= delta_time
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def render(self, renderer):
        """Render all particles"""
        for particle in self.particles:
            alpha = particle['life'] / particle['max_life']
            size = particle['size'] * alpha
            if size > 0.5:
                renderer.draw_circle(particle['position'], size, particle['color'])


class Player(GameObject):
    """Enhanced player with particle effects"""
    
    def __init__(self, name: str = "Player"):
        super().__init__(name)
        self.speed = 250.0
        self.rotation_speed = 4.0
        self.health = 100
        self.max_health = 100
        self.score = 0
        self.invulnerable_time = 0.0
        self.particle_system = None
        
        sprite = Sprite(color='#00FF00', size=Vector2(30, 30))
        self.add_component(sprite)
        self.transform.position = Vector2(400, 300)
    
    def take_damage(self, damage: int):
        """Take damage and become briefly invulnerable"""
        if self.invulnerable_time <= 0:
            self.health -= damage
            self.invulnerable_time = 1.0
            
            # Emit damage particles
            if self.particle_system:
                for _ in range(10):
                    vel = Vector2.from_angle(random.uniform(0, 2 * math.pi), random.uniform(50, 150))
                    self.particle_system.emit_particle(self.transform.position, vel, '#FF0000', 1.0)
    
    def add_score(self, points: int):
        """Add score and emit celebration particles"""
        self.score += points
        if self.particle_system:
            for _ in range(5):
                vel = Vector2.from_angle(random.uniform(0, 2 * math.pi), random.uniform(30, 80))
                self.particle_system.emit_particle(self.transform.position, vel, '#FFD700', 0.8)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if self.invulnerable_time > 0:
            self.invulnerable_time -= delta_time
            
            # Flash when invulnerable
            sprite = self.get_component(Sprite)
            if sprite:
                if int(self.invulnerable_time * 10) % 2:
                    sprite.color = '#FFFFFF'
                else:
                    sprite.color = '#00FF00'
        else:
            sprite = self.get_component(Sprite)
            if sprite:
                sprite.color = '#00FF00'
        
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
            
            # Wrap around screen
            pos = self.transform.position
            if pos.x < -20: pos.x = 820
            elif pos.x > 820: pos.x = -20
            if pos.y < -20: pos.y = 620
            elif pos.y > 620: pos.y = -20


class Enemy(GameObject):
    """Enhanced enemy with AI and particle effects"""
    
    def __init__(self, name: str = "Enemy", center: Vector2 = None, radius: float = 100):
        super().__init__(name)
        self.center = center or Vector2(400, 300)
        self.radius = radius
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.5, 3.0)
        self.health = 50
        self.damage_timer = 0.0
        
        sprite = Sprite(color='#FF3232', size=Vector2(25, 25), shape='circle')
        self.add_component(sprite)
        
    def take_damage(self, damage: int):
        """Take damage"""
        self.health -= damage
        self.damage_timer = 0.2
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if self.damage_timer > 0:
            self.damage_timer -= delta_time
            sprite = self.get_component(Sprite)
            if sprite:
                sprite.color = '#FFFFFF' if int(self.damage_timer * 20) % 2 else '#FF3232'
        else:
            sprite = self.get_component(Sprite)
            if sprite:
                sprite.color = '#FF3232'
        
        # Move in orbit
        self.angle += self.speed * delta_time
        offset = Vector2.from_angle(self.angle, self.radius)
        self.transform.position = self.center + offset
        
        # Face movement direction
        self.transform.rotation = self.angle + math.pi / 2
        
        # Check if dead
        if self.health <= 0:
            # Find player and add score
            if self.scene:
                player = self.scene.find_object("Player")
                if player and hasattr(player, 'add_score'):
                    player.add_score(10)
            
            self.destroy()


class UIElement(GameObject):
    """Base UI element"""
    
    def __init__(self, name: str = "UIElement"):
        super().__init__(name)
        self.text = ""
        self.font_size = 16
        self.color = '#FFFFFF'
        self.background_color = None
        
    def render(self, renderer):
        if self.background_color:
            # Draw background
            text_size = Vector2(len(self.text) * self.font_size * 0.6, self.font_size * 1.2)
            bg_pos = self.transform.position - text_size / 2
            renderer.draw_rect(bg_pos, text_size, self.background_color)
        
        # Draw text
        renderer.draw_text(self.transform.position, self.text, self.color, self.font_size)


class Button(UIElement):
    """Interactive button"""
    
    def __init__(self, name: str = "Button", text: str = "Button", callback=None):
        super().__init__(name)
        self.text = text
        self.callback = callback
        self.size = Vector2(120, 40)
        self.is_hovered = False
        self.is_pressed = False
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if hasattr(self.scene, 'engine'):
            input_manager = self.scene.engine.input_manager
            mouse_pos = input_manager.get_mouse_position()
            
            # Check if mouse is over button
            button_rect = (
                self.transform.position.x - self.size.x / 2,
                self.transform.position.y - self.size.y / 2,
                self.size.x,
                self.size.y
            )
            
            self.is_hovered = (
                button_rect[0] <= mouse_pos.x <= button_rect[0] + button_rect[2] and
                button_rect[1] <= mouse_pos.y <= button_rect[1] + button_rect[3]
            )
            
            # Check for click
            if self.is_hovered and input_manager.is_mouse_button_just_pressed('left'):
                self.is_pressed = True
                print(f"Button '{self.text}' clicked!")
                if self.callback:
                    print(f"Executing callback for button '{self.text}'")
                    self.callback()
                else:
                    print(f"No callback set for button '{self.text}'")
            elif not input_manager.is_mouse_button_pressed('left'):
                self.is_pressed = False
    
    def render(self, renderer):
        # Choose colors based on state
        bg_color = '#666666'
        text_color = '#FFFFFF'
        
        if self.is_pressed:
            bg_color = '#333333'
        elif self.is_hovered:
            bg_color = '#888888'
        
        # Draw button background
        button_pos = self.transform.position - self.size / 2
        renderer.draw_rectangle(button_pos, self.size, bg_color, 0.0, '#FFFFFF')
        
        # Draw button text centered
        renderer.draw_text(self.transform.position, self.text, text_color, 14)


class MenuScene(Scene):
    """Main menu scene"""
    
    def __init__(self):
        super().__init__("Menu")
        
    def initialize(self):
        super().initialize()
        
        # Title
        title = UIElement("Title")
        title.text = "SPACE DEFENSE"
        title.font_size = 32
        title.color = '#00FFFF'
        title.transform.position = Vector2(400, 200)
        self.add_object(title)
        
        # Instructions
        instructions = [
            "Use WASD or Arrow Keys to move",
            "Use Q/E to rotate",
            "Avoid the red enemies!",
            "Survive as long as possible"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_obj = UIElement(f"Instruction_{i}")
            inst_obj.text = instruction
            inst_obj.font_size = 14
            inst_obj.color = '#CCCCCC'
            inst_obj.transform.position = Vector2(400, 280 + i * 25)
            self.add_object(inst_obj)
        
        # Start button
        def start_game():
            if hasattr(self, 'engine') and self.engine:
                game_scene = GameScene()
                self.engine.load_scene(game_scene)
            else:
                print("Error: Engine reference not found")
        
        start_button = Button("StartButton", "START GAME", start_game)
        start_button.transform.position = Vector2(400, 450)
        self.add_object(start_button)


class GameScene(Scene):
    """Main game scene"""
    
    def __init__(self):
        super().__init__("Game")
        self.wave = 1
        self.enemies_remaining = 0
        self.wave_timer = 0.0
        self.game_time = 0.0
        
    def initialize(self):
        super().initialize()
        
        # Create particle system
        particle_system = ParticleSystem("Particles")
        self.add_object(particle_system)
        
        # Create player
        player = Player("Player")
        player.particle_system = particle_system
        self.add_object(player)
        
        # Start first wave
        self.start_wave()
        
        # UI Elements
        self.create_ui()
    
    def create_ui(self):
        """Create game UI"""
        # Health bar background
        health_bg = UIElement("HealthBG")
        health_bg.transform.position = Vector2(100, 30)
        self.add_object(health_bg)
        
        # Score display
        score_display = UIElement("ScoreDisplay")
        score_display.transform.position = Vector2(400, 30)
        self.add_object(score_display)
        
        # Wave display
        wave_display = UIElement("WaveDisplay")
        wave_display.transform.position = Vector2(700, 30)
        self.add_object(wave_display)
    
    def start_wave(self):
        """Start a new wave of enemies"""
        self.enemies_remaining = 3 + self.wave
        
        for i in range(self.enemies_remaining):
            angle = (i / self.enemies_remaining) * 2 * math.pi
            center = Vector2(400, 300) + Vector2.from_angle(angle, 150 + self.wave * 20)
            enemy = Enemy(f"Enemy_{self.wave}_{i}", center, 40 + random.uniform(-20, 20))
            self.add_object(enemy)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        self.game_time += delta_time
        self.wave_timer += delta_time
        
        # Check for player death
        player = self.find_object("Player")
        if player and player.health <= 0:
            if hasattr(self, 'engine'):
                game_over_scene = GameOverScene(player.score, self.game_time)
                self.engine.load_scene(game_over_scene)
            return
        
        # Check for wave completion
        enemies = self.find_objects_with_tag("enemy")
        if not enemies and self.wave_timer > 2.0:
            self.wave += 1
            self.wave_timer = 0.0
            self.start_wave()
        
        # Collision detection
        if player:
            player_pos = player.transform.position
            for enemy in enemies:
                enemy_pos = enemy.transform.position
                distance = player_pos.distance_to(enemy_pos)
                if distance < 25:
                    player.take_damage(20)
        
        # Update UI
        self.update_ui()
    
    def update_ui(self):
        """Update UI elements"""
        player = self.find_object("Player")
        if not player:
            return
        
        # Health bar
        health_bg = self.find_object("HealthBG")
        if health_bg:
            health_percent = player.health / player.max_health
            health_bg.text = f"Health: {'█' * int(health_percent * 10)}{'░' * (10 - int(health_percent * 10))}"
            health_bg.color = '#00FF00' if health_percent > 0.5 else '#FFFF00' if health_percent > 0.25 else '#FF0000'
        
        # Score
        score_display = self.find_object("ScoreDisplay")
        if score_display:
            score_display.text = f"Score: {player.score}"
            score_display.color = '#FFFFFF'
        
        # Wave
        wave_display = self.find_object("WaveDisplay")
        if wave_display:
            wave_display.text = f"Wave: {self.wave}"
            wave_display.color = '#FFFFFF'


class GameOverScene(Scene):
    """Game over scene"""
    
    def __init__(self, final_score: int = 0, survival_time: float = 0.0):
        super().__init__("GameOver")
        self.final_score = final_score
        self.survival_time = survival_time
    
    def initialize(self):
        super().initialize()
        
        # Game Over title
        title = UIElement("GameOverTitle")
        title.text = "GAME OVER"
        title.font_size = 36
        title.color = '#FF0000'
        title.transform.position = Vector2(400, 200)
        self.add_object(title)
        
        # Final score
        score_text = UIElement("FinalScore")
        score_text.text = f"Final Score: {self.final_score}"
        score_text.font_size = 20
        score_text.color = '#FFFFFF'
        score_text.transform.position = Vector2(400, 280)
        self.add_object(score_text)
        
        # Survival time
        time_text = UIElement("SurvivalTime")
        time_text.text = f"Survived: {self.survival_time:.1f} seconds"
        time_text.font_size = 16
        time_text.color = '#CCCCCC'
        time_text.transform.position = Vector2(400, 320)
        self.add_object(time_text)
        
        # Restart button
        def restart_game():
            if hasattr(self, 'engine'):
                game_scene = GameScene()
                self.engine.load_scene(game_scene)
        
        restart_button = Button("RestartButton", "PLAY AGAIN", restart_game)
        restart_button.transform.position = Vector2(300, 400)
        self.add_object(restart_button)
        
        # Menu button
        def return_to_menu():
            if hasattr(self, 'engine'):
                menu_scene = MenuScene()  
                self.engine.load_scene(menu_scene)
        
        menu_button = Button("MenuButton", "MAIN MENU", return_to_menu)
        menu_button.transform.position = Vector2(500, 400)
        self.add_object(menu_button)


class CompleteGame(GameEngine):
    """Complete game with multiple scenes"""
    
    def initialize(self):
        """Initialize the game with menu scene"""
        menu_scene = MenuScene()
        menu_scene.engine = self  # Give scene access to engine
        self.load_scene(menu_scene)
        
        print("Space Defense - Complete Game")
        print("Starting at main menu...")
    
    def update(self, delta_time: float):
        """Game update logic"""
        # Global controls
        if self.input_manager.is_key_just_pressed('escape'):
            # Return to menu or quit
            if self.current_scene.name != "Menu":
                menu_scene = MenuScene()
                menu_scene.engine = self
                self.load_scene(menu_scene)
            else:
                self.quit()
        
        if self.input_manager.is_key_just_pressed('f11'):
            self.toggle_fullscreen()
        
        # Update window title with scene info
        fps = self.get_fps()
        scene_name = self.current_scene.name if self.current_scene else "None"
        self.window.set_title(f"Space Defense - {scene_name} - FPS: {fps:.1f}")
    
    def load_scene(self, scene):
        """Load a new scene"""
        if self.current_scene:
            self.current_scene.cleanup()
        
        self.current_scene = scene
        scene.engine = self  # Give scene access to engine
        scene.initialize()
        
        # Ensure all objects in the scene have access to the engine
        for obj in scene.game_objects:
            if hasattr(obj, 'scene'):
                obj.scene = scene


if __name__ == "__main__":
    # Create and run the complete game
    game = CompleteGame("Space Defense - Complete Game", (800, 600), 60)
    game.run()
