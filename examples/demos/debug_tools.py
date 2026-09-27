"""Runnable demonstration of the built-in debugging tools.

Every GameEngine already owns a DebugOverlay -- this demo just gives it
something worth looking at: moving colliders, a rising object count, and an
occasional deliberate hitch to trigger the slow-frame warning.
"""

import random
import time

from engine import AABBCollider, CircleCollider, GameEngine, GameObject, Sprite, Vector2


class Ball(GameObject):
    """A circle collider that bounces around the screen."""

    def __init__(self, index):
        super().__init__(f'Ball_{index}')
        self.velocity = Vector2(random.uniform(-120, 120), random.uniform(-120, 120))
        self.radius = 12
        self.add_component(Sprite(color='#3388FF', size=Vector2(self.radius * 2, self.radius * 2), shape='circle'))
        collider = self.add_component(CircleCollider(self.radius))
        collider.on_enter(self._flash)
        self.transform.position = Vector2(random.uniform(100, 700), random.uniform(100, 500))

    def _flash(self, other):
        sprite = self.get_component(Sprite)
        sprite.color = '#FF3333'

    def update(self, delta_time):
        super().update(delta_time)
        sprite = self.get_component(Sprite)
        sprite.color = '#3388FF'

        position = self.transform.position + self.velocity * delta_time
        if position.x < self.radius or position.x > 800 - self.radius:
            self.velocity.x = -self.velocity.x
        if position.y < self.radius or position.y > 600 - self.radius:
            self.velocity.y = -self.velocity.y
        position.x = max(self.radius, min(800 - self.radius, position.x))
        position.y = max(self.radius, min(600 - self.radius, position.y))
        self.transform.position = position


class Wall(GameObject):
    """A static box collider the balls bounce off of visually."""

    def __init__(self, name, position, size):
        super().__init__(name)
        self.add_component(Sprite(color='#555577', size=size))
        self.add_component(AABBCollider(size))
        self.transform.position = position


class HitchSimulator(GameObject):
    """Deliberately stalls for a moment every few seconds.

    This is the only thing in this demo that isn't "real" game content --
    it exists purely to trigger the DebugOverlay's automatic slow-frame
    warning so you can see it fire in the console without waiting for a
    real performance problem.
    """

    def __init__(self, interval=3.0, stall_seconds=0.08):
        super().__init__('HitchSimulator')
        self.interval = interval
        self.stall_seconds = stall_seconds
        self.timer = 0.0

    def update(self, delta_time):
        super().update(delta_time)
        self.timer += delta_time
        if self.timer >= self.interval:
            self.timer = 0.0
            time.sleep(self.stall_seconds)


class DebugToolsDemo(GameEngine):
    """Demo showcasing the stats overlay, collider outlines, log-level
    cycling, and scene inspection built into every GameEngine."""

    def initialize(self):
        for index in range(8):
            self.current_scene.add_object(Ball(index))

        self.current_scene.add_object(Wall('LeftWall', Vector2(60, 300), Vector2(20, 200)))
        self.current_scene.add_object(Wall('RightWall', Vector2(740, 300), Vector2(20, 200)))
        self.current_scene.add_object(HitchSimulator())

        print("Debug Tools Demo")
        print("F3 - Toggle stats overlay (FPS, frame time, object/collider counts)")
        print("F4 - Toggle collider outlines")
        print("F5 - Cycle log level (watch the console)")
        print("F6 - Dump the current scene to the console")
        print("ESC - Quit")
        print()
        print("A brief hitch is simulated every 3 seconds to trigger the")
        print("automatic slow-frame warning in the console.")

    def update(self, delta_time):
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()


if __name__ == "__main__":
    DebugToolsDemo().run()
