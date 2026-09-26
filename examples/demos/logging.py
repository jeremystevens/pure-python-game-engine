
"""
Example demonstrating the logging system
"""
from engine import GameEngine, GameObject, Scene, Sprite, Vector2
from engine.core.logger import LogLevel, get_logger, set_global_log_level


class LoggingTestObject(GameObject):
    """Test object that demonstrates logging"""
    
    def __init__(self, name: str = "LoggingTest"):
        super().__init__(name)
        
        # Get a logger for this object
        self.logger = get_logger("TestObject")
        
        sprite = Sprite(color='#FF6B6B', size=Vector2(50, 50))
        self.add_component(sprite)
        self.transform.position = Vector2(400, 300)
        
        self.logger.debug("LoggingTestObject created")
        self.update_timer = 0.0
        
    def update(self, delta_time: float):
        super().update(delta_time)
        
        self.update_timer += delta_time
        
        # Log different levels based on time
        if int(self.update_timer) % 5 == 0 and self.update_timer - delta_time < int(self.update_timer):
            if int(self.update_timer) % 20 == 0:
                self.logger.error("This is an error message (every 20 seconds)")
            elif int(self.update_timer) % 15 == 0:
                self.logger.warning("This is a warning message (every 15 seconds)")
            elif int(self.update_timer) % 10 == 0:
                self.logger.info("This is an info message (every 10 seconds)")
            else:
                self.logger.debug("This is a debug message (every 5 seconds)")


class LoggingDemo(GameEngine):
    """Demo showcasing the logging system"""
    
    def initialize(self):
        """Initialize the demo"""
        # Get demo logger
        self.demo_logger = get_logger("Demo")
        
        self.demo_logger.info("Initializing logging demonstration")
        
        # Create test object
        test_obj = LoggingTestObject("TestObj")
        self.current_scene.add_object(test_obj)
        self.current_scene.engine = self
        
        # Demonstrate different log levels
        self.demo_logger.debug("This is a debug message")
        self.demo_logger.info("This is an info message")
        self.demo_logger.warning("This is a warning message")
        self.demo_logger.error("This is an error message")
        
        print("\nLogging System Demo")
        print("Controls:")
        print("  1 - Set log level to DEBUG")
        print("  2 - Set log level to INFO")
        print("  3 - Set log level to WARNING")
        print("  4 - Set log level to ERROR")
        print("  C - Toggle colors")
        print("  T - Toggle timestamps")
        print("  ESC - Quit")
        print("\nWatch the console for automatic log messages!")
        
    def update(self, delta_time: float):
        """Update demo"""
        # Log level controls
        if self.input_manager.is_key_just_pressed('1'):
            set_global_log_level(LogLevel.DEBUG)
            self.demo_logger.info("Log level set to DEBUG")
            
        if self.input_manager.is_key_just_pressed('2'):
            set_global_log_level(LogLevel.INFO)
            self.demo_logger.info("Log level set to INFO")
            
        if self.input_manager.is_key_just_pressed('3'):
            set_global_log_level(LogLevel.WARNING)
            self.demo_logger.warning("Log level set to WARNING")
            
        if self.input_manager.is_key_just_pressed('4'):
            set_global_log_level(LogLevel.ERROR)
            self.demo_logger.error("Log level set to ERROR")
        
        # Toggle features
        if self.input_manager.is_key_just_pressed('c'):
            # This is a simple toggle - in a real implementation you'd track state
            from engine.core.logger import enable_colors
            enable_colors(False)  # For demo, just disable colors
            self.demo_logger.info("Colors toggled")
            
        if self.input_manager.is_key_just_pressed('t'):
            from engine.core.logger import configure_timestamps
            configure_timestamps(False)  # For demo, just disable timestamps
            self.demo_logger.info("Timestamps toggled")
        
        # Quit
        if self.input_manager.is_key_just_pressed('escape'):
            self.demo_logger.info("Logging demo ending...")
            self.quit()
        
        # Update window title
        fps = self.get_fps()
        self.window.set_title(f"Logging Demo - FPS: {fps:.1f}")


if __name__ == "__main__":
    demo = LoggingDemo("Logging System Demo", (800, 600), 60)
    demo.run()
