
"""
Example demonstrating sprite atlas and animation features
"""
from engine import GameEngine, GameObject, Vector2, Sprite
from engine.graphics.sprite import SpriteAtlas, SpriteAnimation

class AnimatedSprite(GameObject):
    """Game object with animated sprite"""
    
    def __init__(self, name: str = "AnimatedSprite"):
        super().__init__(name)
        
        # Create sprite with animation support
        self.sprite = Sprite(color='#FF6B6B', size=Vector2(60, 60))
        self.add_component(self.sprite)
        
        # Create a simple sprite atlas
        atlas = SpriteAtlas(Vector2(256, 256))
        
        # Add different colored frames for animation
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        for i, color in enumerate(colors):
            atlas.add_sprite(f"frame_{i}", Vector2(i * 50, 0), Vector2(50, 50), color)
        
        self.sprite.set_sprite_atlas(atlas)
        
        # Create animation
        self.sprite.add_animation("pulse", list(range(5)), 0.2, True)
        self.sprite.play_animation("pulse")
        
        # Add shader effects
        self.sprite.set_brightness(1.2)
        
        # Set position
        self.transform.position = Vector2(400, 300)

class AtlasDemo(GameEngine):
    """Demo showcasing sprite atlas and animations"""
    
    def initialize(self):
        """Initialize the demo"""
        # Create animated sprites
        for i in range(3):
            sprite = AnimatedSprite(f"AnimatedSprite_{i}")
            sprite.transform.position = Vector2(200 + i * 200, 300)
            self.current_scene.add_object(sprite)
        
        print("Sprite Atlas & Animation Demo")
        print("Watch the animated sprites with different shader effects!")
        print("Press ESC to quit")
    
    def update(self, delta_time: float):
        """Update demo"""
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()

if __name__ == "__main__":
    demo = AtlasDemo("Sprite Atlas & Animation Demo", (800, 600), 60)
    demo.run()
