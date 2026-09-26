"""
Classic Breakout Game - Atari 2600 Style
Built using the Pure Python 2D Game Engine
"""
import math
import random
from engine import GameEngine, GameObject, Vector2, Sprite, SoundGenerator
from engine.scene.game_object import Component


class Ball(GameObject):
    """Game ball with physics"""
    
    def __init__(self):
        super().__init__("Ball")
        self.velocity = Vector2(150, -200)  # Start moving up and right
        self.speed = 200
        self.radius = 4
        
        # White square ball (Atari 2600 style)
        sprite = Sprite(color='#FFFFFF', size=Vector2(8, 8))
        self.add_component(sprite)
        
        # Start position
        self.transform.position = Vector2(400, 500)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        # Move ball
        self.transform.position += self.velocity * delta_time
        
        # Screen boundaries
        pos = self.transform.position
        
        # Left and right walls
        if pos.x <= self.radius or pos.x >= 800 - self.radius:
            self.velocity.x = -self.velocity.x
            pos.x = max(self.radius, min(800 - self.radius, pos.x))
            # Play wall bounce sound
            if hasattr(self.scene, 'engine') and hasattr(self.scene.engine, 'sound_generator'):
                self.scene.engine.sound_generator.play_sound("wall_bounce")
                print("*wall bounce*")  # Visual feedback
        
        # Top wall
        if pos.y <= self.radius:
            self.velocity.y = -self.velocity.y
            pos.y = self.radius
            # Play wall bounce sound
            if hasattr(self.scene, 'engine') and hasattr(self.scene.engine, 'sound_generator'):
                self.scene.engine.sound_generator.play_sound("wall_bounce")
                print("*wall bounce*")  # Visual feedback
        
        # Bottom - ball is lost (don't reset here, let main game handle it)
        # The main game loop will detect this and handle life reduction
    
    def reset_ball(self):
        """Reset ball to starting position"""
        self.transform.position = Vector2(400, 500)
        # Random starting direction
        angle = random.uniform(-math.pi/4, -3*math.pi/4)  # Upward angles
        self.velocity = Vector2.from_angle(angle, self.speed)
    
    def bounce_off_paddle(self, paddle_pos, paddle_width):
        """Bounce off paddle with angle based on hit position"""
        # Calculate hit position relative to paddle center
        hit_pos = (self.transform.position.x - paddle_pos.x) / (paddle_width / 2)
        hit_pos = max(-1, min(1, hit_pos))  # Clamp to [-1, 1]
        
        # Calculate bounce angle (more extreme angles at paddle edges)
        bounce_angle = hit_pos * math.pi / 3  # Max 60 degrees
        
        # Set new velocity with upward direction
        speed = self.velocity.magnitude
        self.velocity = Vector2(
            math.sin(bounce_angle) * speed,
            -abs(math.cos(bounce_angle) * speed)
        )


class Paddle(GameObject):
    """Player paddle"""
    
    def __init__(self):
        super().__init__("Paddle")
        self.width = 64
        self.height = 12
        self.speed = 400
        
        # Orange paddle (Atari 2600 color)
        sprite = Sprite(color='#FF8C00', size=Vector2(self.width, self.height))
        self.add_component(sprite)
        
        # Starting position
        self.transform.position = Vector2(400, 550)
    
    def update(self, delta_time: float):
        super().update(delta_time)
        
        if not hasattr(self.scene, 'engine'):
            return
        
        input_manager = self.scene.engine.input_manager
        
        # Movement
        movement = 0
        if input_manager.is_key_pressed('left') or input_manager.is_key_pressed('a'):
            movement = -1
        if input_manager.is_key_pressed('right') or input_manager.is_key_pressed('d'):
            movement = 1
        
        # Move paddle
        if movement != 0:
            self.transform.position.x += movement * self.speed * delta_time
            
            # Keep paddle on screen
            half_width = self.width / 2
            self.transform.position.x = max(half_width, 
                min(800 - half_width, self.transform.position.x))


class Brick(GameObject):
    """Individual brick"""
    
    def __init__(self, color, points, x, y):
        super().__init__("Brick")
        self.points = points
        self.width = 40
        self.height = 16
        
        sprite = Sprite(color=color, size=Vector2(self.width, self.height))
        self.add_component(sprite)
        
        self.transform.position = Vector2(x, y)
    
    def hit(self):
        """Brick is hit by ball"""
        return self.points


class ScoreDisplay(GameObject):
    """Score display using rectangles to form numbers"""
    
    def __init__(self):
        super().__init__("ScoreDisplay")
        self.score = 0
        self.lives = 3
        self.transform.position = Vector2(50, 30)
    
    def render(self, renderer):
        """Render score and lives as text"""
        # In a real Atari 2600, this would be rendered as sprites
        # For simplicity, we'll render as text
        renderer.draw_text(Vector2(50, 30), f"SCORE: {self.score:04d}", '#FFFFFF', 16)
        renderer.draw_text(Vector2(650, 30), f"LIVES: {self.lives}", '#FFFFFF', 16)


class BreakoutGame(GameEngine):
    """Main Breakout game"""
    
    def __init__(self):
        super().__init__("Breakout - Atari 2600 Style", (800, 600), 60)
        self.score = 0
        self.lives = 3
        self.ball = None
        self.paddle = None
        self.bricks = []
        self.score_display = None
        self.game_state = "playing"  # playing, game_over, level_complete
        
        # Initialize sound system
        self.sound_generator = SoundGenerator()
        self.create_breakout_sounds()
    
    def create_breakout_sounds(self):
        """Create Atari 2600 Breakout-style sound effects"""
        from engine.audio.sound_generator import Sound
        
        # Paddle hit sound - low frequency blip
        paddle_sound = Sound("paddle_hit")
        paddle_sound.generate_tone(120, 0.1, 'square', 0.4)
        self.sound_generator.register_sound(paddle_sound)
        
        # Brick hit sounds - different tones for different colored bricks
        # High value bricks (red/orange) - higher pitch
        high_brick_sound = Sound("high_brick")
        high_brick_sound.generate_tone(800, 0.08, 'square', 0.3)
        self.sound_generator.register_sound(high_brick_sound)
        
        # Medium value bricks (yellow/green) - medium pitch
        mid_brick_sound = Sound("mid_brick")
        mid_brick_sound.generate_tone(600, 0.08, 'square', 0.3)
        self.sound_generator.register_sound(mid_brick_sound)
        
        # Low value bricks (blue/purple/pink) - lower pitch
        low_brick_sound = Sound("low_brick")
        low_brick_sound.generate_tone(400, 0.08, 'square', 0.3)
        self.sound_generator.register_sound(low_brick_sound)
        
        # Wall bounce sound - quick high blip
        wall_sound = Sound("wall_bounce")
        wall_sound.generate_tone(1000, 0.05, 'square', 0.2)
        self.sound_generator.register_sound(wall_sound)
        
        # Ball lost sound - descending tone
        lose_ball_sound = Sound("lose_ball")
        lose_ball_sound.generate_sweep(400, 100, 0.5, 'square', 0.4)
        self.sound_generator.register_sound(lose_ball_sound)
        
        # Game over sound - low descending sweep
        game_over_sound = Sound("game_over")
        game_over_sound.generate_sweep(300, 50, 1.0, 'square', 0.5)
        self.sound_generator.register_sound(game_over_sound)
        
        # Level complete sound - ascending sweep
        level_complete_sound = Sound("level_complete")
        level_complete_sound.generate_sweep(200, 800, 1.5, 'square', 0.4)
        self.sound_generator.register_sound(level_complete_sound)

    def initialize(self):
        """Initialize the game"""
        self.setup_game()
        
        print("Breakout - Atari 2600 Style")
        print("Controls:")
        print("  A/D or Arrow Keys - Move paddle")
        print("  ESC - Quit")
        print("Sound effects enabled!")
    
    def setup_game(self):
        """Set up game objects"""
        # Clear existing objects
        if self.current_scene:
            self.current_scene.game_objects.clear()
        
        # Create paddle
        self.paddle = Paddle()
        self.current_scene.add_object(self.paddle)
        
        # Create ball
        self.ball = Ball()
        self.current_scene.add_object(self.ball)
        
        # Create score display
        self.score_display = ScoreDisplay()
        self.score_display.score = self.score
        self.score_display.lives = self.lives
        self.current_scene.add_object(self.score_display)
        
        # Create bricks in Atari 2600 style layout
        self.create_bricks()
        
        # Give scene access to engine
        self.current_scene.engine = self
    
    def create_bricks(self):
        """Create the brick wall in Atari 2600 colors and layout"""
        self.bricks = []
        
        # Atari 2600 Breakout colors (top to bottom)
        brick_colors = [
            ('#FF0000', 7),  # Red - 7 points
            ('#FF8C00', 7),  # Orange - 7 points  
            ('#FFFF00', 5),  # Yellow - 5 points
            ('#00FF00', 5),  # Green - 5 points
            ('#0000FF', 3),  # Blue - 3 points
            ('#8A2BE2', 3),  # Purple - 3 points
            ('#FF69B4', 1),  # Pink - 1 point
            ('#FF1493', 1),  # Deep Pink - 1 point
        ]
        
        # Create 8 rows of bricks
        start_x = 100
        start_y = 80
        brick_width = 40
        brick_height = 16
        bricks_per_row = 15
        
        for row in range(8):
            color, points = brick_colors[row]
            for col in range(bricks_per_row):
                x = start_x + col * (brick_width + 2)
                y = start_y + row * (brick_height + 2)
                
                brick = Brick(color, points, x, y)
                self.bricks.append(brick)
                self.current_scene.add_object(brick)
    
    def update(self, delta_time: float):
        """Game update logic"""
        super().update(delta_time)
        
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        
        if self.game_state != "playing":
            return
        
        # Ball-paddle collision
        if self.ball and self.paddle:
            ball_pos = self.ball.transform.position
            paddle_pos = self.paddle.transform.position
            
            # Check collision with paddle
            if (ball_pos.y + self.ball.radius > paddle_pos.y - self.paddle.height/2 and
                ball_pos.y - self.ball.radius < paddle_pos.y + self.paddle.height/2 and
                ball_pos.x > paddle_pos.x - self.paddle.width/2 and
                ball_pos.x < paddle_pos.x + self.paddle.width/2 and
                self.ball.velocity.y > 0):  # Ball moving down
                
                self.ball.bounce_off_paddle(paddle_pos, self.paddle.width)
                # Play paddle hit sound
                self.sound_generator.play_sound("paddle_hit")
                print("*paddle hit*")  # Visual feedback
        
        # Ball-brick collisions
        if self.ball:
            ball_pos = self.ball.transform.position
            
            for brick in self.bricks[:]:  # Copy list to avoid modification during iteration
                brick_pos = brick.transform.position
                
                # Simple AABB collision detection
                if (ball_pos.x + self.ball.radius > brick_pos.x - brick.width/2 and
                    ball_pos.x - self.ball.radius < brick_pos.x + brick.width/2 and
                    ball_pos.y + self.ball.radius > brick_pos.y - brick.height/2 and
                    ball_pos.y - self.ball.radius < brick_pos.y + brick.height/2):
                    
                    # Remove brick and play appropriate sound
                    points = brick.hit()
                    self.score += points
                    
                    # Play sound based on brick value (Atari 2600 style)
                    if points >= 7:  # Red/Orange bricks
                        self.sound_generator.play_sound("high_brick")
                        print(f"*high brick hit* +{points} points")
                    elif points >= 5:  # Yellow/Green bricks
                        self.sound_generator.play_sound("mid_brick")
                        print(f"*mid brick hit* +{points} points")
                    else:  # Blue/Purple/Pink bricks
                        self.sound_generator.play_sound("low_brick")
                        print(f"*low brick hit* +{points} points")
                    
                    self.bricks.remove(brick)
                    brick.destroy()
                    self.current_scene.remove_object(brick)
                    
                    # Bounce ball (simplified - just reverse Y velocity)
                    self.ball.velocity.y = -self.ball.velocity.y
                    
                    # Increase ball speed slightly (Atari 2600 behavior)
                    self.ball.velocity *= 1.02
                    
                    break
        
        # Check for ball lost
        if self.ball and self.ball.transform.position.y > 600:
            self.lives -= 1
            self.sound_generator.play_sound("lose_ball")
            print(f"*lose ball* Lives remaining: {self.lives}")  # Visual feedback
            
            if self.lives <= 0:
                self.game_state = "game_over"
                self.sound_generator.play_sound("game_over")
                print(f"Game Over! Final Score: {self.score}")
            else:
                self.ball.reset_ball()
        
        # Check for level complete
        if len(self.bricks) == 0:
            self.game_state = "level_complete"
            self.sound_generator.play_sound("level_complete")
            print(f"Level Complete! Score: {self.score}")
            # In a full game, you'd start the next level
        
        # Update score display
        if self.score_display:
            self.score_display.score = self.score
            self.score_display.lives = self.lives
    
    def render(self):
        """Custom rendering"""
        # Draw game over or level complete messages
        if self.game_state == "game_over":
            self.renderer.draw_text(Vector2(400, 300), "GAME OVER", '#FFFFFF', 32)
            self.renderer.draw_text(Vector2(400, 340), f"Final Score: {self.score}", '#FFFFFF', 16)
        elif self.game_state == "level_complete":
            self.renderer.draw_text(Vector2(400, 300), "LEVEL COMPLETE!", '#FFFFFF', 32)
            self.renderer.draw_text(Vector2(400, 340), f"Score: {self.score}", '#FFFFFF', 16)


if __name__ == "__main__":
    game = BreakoutGame()
    game.run()
