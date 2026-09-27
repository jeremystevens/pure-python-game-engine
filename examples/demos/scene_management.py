"""Runnable demonstration of the named scene registry and scene stack."""

from engine import GameEngine, GameObject, Scene, Sprite, Vector2


class PersistentCounter(GameObject):
    """Survives scene replacement to prove persistent objects transfer safely."""

    def __init__(self):
        super().__init__('Counter')
        self.set_persistent()
        self.count = 0
        self.add_component(Sprite(color='#FFD700', size=Vector2(30, 30), shape='circle'))
        self.transform.position = Vector2(400, 480)

    def update(self, delta_time):
        super().update(delta_time)
        if hasattr(self.scene, 'engine') and self.scene.engine.input_manager.is_key_just_pressed('space'):
            self.count += 1


class HubScene(Scene):
    """Home base. Creates the persistent counter once, then reuses it forever."""

    def __init__(self):
        super().__init__('Hub')

    def on_initialize(self):
        if not self.find_object('Counter'):
            self.add_object(PersistentCounter())


class LevelScene(Scene):
    """A named, factory-created scene with its own throwaway content."""

    def __init__(self, display_name, color):
        super().__init__(display_name)
        self.color = color

    def on_initialize(self):
        marker = GameObject('LevelMarker')
        marker.add_component(Sprite(color=self.color, size=Vector2(140, 90)))
        marker.transform.position = Vector2(400, 180)
        self.add_object(marker)


class PauseOverlayVisual(GameObject):
    """Draws a box in the gap between the level marker and the counter,
    so both remain visibly rendered underneath while paused."""

    def render(self, renderer):
        renderer.draw_rectangle(Vector2(400, 320), Vector2(340, 140), '#1A1A2E', outline='#FFFF00', width=2)
        renderer.draw_text(Vector2(400, 300), 'PAUSED', '#FFFF00', 28, 'center')
        renderer.draw_text(Vector2(400, 335), 'Press O to resume', '#FFFFFF', 14, 'center')


class PauseOverlay(Scene):
    """Pushed on top of whichever scene is active; pauses it automatically."""

    def __init__(self):
        super().__init__('Pause')

    def on_initialize(self):
        self.add_object(PauseOverlayVisual('PauseVisual'))


class SceneManagementDemo(GameEngine):
    """Demo showcasing the named scene registry and scene stack."""

    def initialize(self):
        self.register_scene('hub', HubScene)
        self.register_scene('level_a', lambda: LevelScene('Level A', '#3388FF'))
        self.register_scene('level_b', lambda: LevelScene('Level B', '#FF6644'))
        self.register_scene('pause', PauseOverlay)
        self.load_scene('hub')

        print("Scene Management Demo")
        print("1 - Load Hub | 2 - Load Level A | 3 - Load Level B  (replace)")
        print("SPACE - Increment the persistent counter (only while not paused)")
        print("P - Push pause overlay | O - Pop pause overlay")
        print("ESC - Quit")

    def update(self, delta_time):
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()
        if self.input_manager.is_key_just_pressed('1'):
            self.load_scene('hub')
        if self.input_manager.is_key_just_pressed('2'):
            self.load_scene('level_a')
        if self.input_manager.is_key_just_pressed('3'):
            self.load_scene('level_b')
        if self.input_manager.is_key_just_pressed('p'):
            self.push_scene('pause')
        if self.input_manager.is_key_just_pressed('o'):
            self.pop_scene()

    def render(self):
        stack = self.scene_manager.scene_stack
        base = stack[0] if stack else None
        counter = base.find_object('Counter') if base else None
        count = counter.count if counter else 0

        self.renderer.draw_text(Vector2(400, 30), 'SCENE MANAGEMENT DEMO', '#FFFFFF', 20, 'center')
        self.renderer.draw_text(
            Vector2(400, 58),
            f"Scene: {self.current_scene.name}   Stack depth: {self.scene_manager.stack_depth}   "
            f"Registered: {', '.join(self.scene_manager.registered_scene_names)}",
            '#80FFB0',
            13,
            'center',
        )
        self.renderer.draw_text(
            Vector2(400, 82),
            f"Persistent counter (same object across every scene change): {count}",
            '#FFD700',
            14,
            'center',
        )
        self.renderer.draw_text(
            Vector2(400, 560),
            '1 Hub   2 Level A   3 Level B   SPACE +1   P Pause   O Resume   ESC Quit',
            '#FFE080',
            13,
            'center',
        )


if __name__ == "__main__":
    SceneManagementDemo().run()
