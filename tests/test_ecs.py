import unittest
from unittest.mock import MagicMock

from engine.ecs.component import Component
from engine.ecs.components import (
    HealthComponent,
    SpriteComponent,
    TagComponent,
    TimerComponent,
    TransformComponent,
    VelocityComponent,
)
from engine.ecs.entity import EntityManager
from engine.ecs.system import System, SystemManager
from engine.ecs.systems import (
    BoundarySystem,
    HealthSystem,
    MovementSystem,
    RenderSystem,
    TimerSystem,
)
from engine.ecs.world import World
from engine.math.vector2 import Vector2


class RecordingComponent(Component):
    def __init__(self):
        super().__init__()
        self.destroy_count = 0

    def destroy(self):
        self.destroy_count += 1


class OtherRecordingComponent(RecordingComponent):
    pass


class RecordingSystem(System):
    def __init__(self, name='recording', priority=0, log=None):
        super().__init__(priority)
        self.name = name
        self.log = log if log is not None else []
        self.start_count = 0
        self.stop_count = 0

    def start(self):
        self.start_count += 1

    def update(self, delta_time):
        self.log.append((self.name, delta_time))

    def stop(self):
        self.stop_count += 1


class OtherRecordingSystem(RecordingSystem):
    pass


class EntityManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = EntityManager()

    def test_entities_have_custom_or_generated_unique_ids(self):
        named = self.manager.create_entity('player')
        first = self.manager.create_entity()
        second = self.manager.create_entity()

        self.assertEqual(named.id, 'player')
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(self.manager.get_all_entities(), [named, first, second])

    def test_components_can_be_added_queried_and_removed(self):
        entity = self.manager.create_entity()
        component = self.manager.add_component(entity, RecordingComponent())

        self.assertIs(component.entity, entity)
        self.assertTrue(self.manager.has_component(entity, RecordingComponent))
        self.assertIs(self.manager.get_component(entity, RecordingComponent), component)
        self.assertEqual(self.manager.get_entities_with_component(RecordingComponent), [entity])

        self.assertTrue(self.manager.remove_component(entity, RecordingComponent))
        self.assertEqual(component.destroy_count, 1)
        self.assertFalse(self.manager.has_component(entity, RecordingComponent))
        self.assertFalse(self.manager.remove_component(entity, RecordingComponent))

    def test_replacing_component_destroys_the_previous_instance(self):
        entity = self.manager.create_entity()
        first = self.manager.add_component(entity, RecordingComponent())
        second = self.manager.add_component(entity, RecordingComponent())

        self.assertEqual(first.destroy_count, 1)
        self.assertIs(self.manager.get_component(entity, RecordingComponent), second)

    def test_multi_component_queries_use_intersection(self):
        both = self.manager.create_entity('both')
        only_first = self.manager.create_entity('first')
        self.manager.add_component(both, RecordingComponent())
        self.manager.add_component(both, OtherRecordingComponent())
        self.manager.add_component(only_first, RecordingComponent())

        self.assertEqual(
            self.manager.get_entities_with_components(RecordingComponent, OtherRecordingComponent),
            [both],
        )
        self.assertEqual(
            self.manager.get_entities_with_components(),
            [both, only_first],
        )

    def test_destroy_entity_destroys_components_and_updates_indices(self):
        entity = self.manager.create_entity()
        component = self.manager.add_component(entity, RecordingComponent())

        self.manager.destroy_entity(entity)

        self.assertEqual(component.destroy_count, 1)
        self.assertNotIn(entity, self.manager.get_all_entities())
        self.assertEqual(self.manager.get_entities_with_component(RecordingComponent), [])


class SystemManagerTests(unittest.TestCase):
    def test_systems_start_sort_update_and_skip_inactive_systems(self):
        log = []
        manager = SystemManager()
        late = RecordingSystem('late', priority=20, log=log)
        early = OtherRecordingSystem('early', priority=10, log=log)
        manager.add_system(late)
        manager.add_system(early)
        late.is_active = False

        manager.update(0.25)

        self.assertEqual(late.start_count, 1)
        self.assertEqual(early.start_count, 1)
        self.assertEqual(manager.systems, [early, late])
        self.assertEqual(log, [('early', 0.25)])

    def test_replacing_and_removing_systems_runs_stop_hooks(self):
        manager = SystemManager()
        first = RecordingSystem()
        second = RecordingSystem()
        manager.add_system(first)

        manager.add_system(second)

        self.assertEqual(first.stop_count, 1)
        self.assertIs(manager.get_system(RecordingSystem), second)
        self.assertTrue(manager.remove_system(RecordingSystem))
        self.assertEqual(second.stop_count, 1)
        self.assertFalse(manager.remove_system(RecordingSystem))

    def test_clear_stops_all_systems(self):
        manager = SystemManager()
        first = RecordingSystem()
        second = OtherRecordingSystem()
        manager.add_system(first)
        manager.add_system(second)

        manager.clear()

        self.assertEqual(first.stop_count, 1)
        self.assertEqual(second.stop_count, 1)
        self.assertEqual(manager.systems, [])


class ComponentAndWorldTests(unittest.TestCase):
    def test_common_components_apply_their_domain_rules(self):
        transform = TransformComponent(Vector2(1, 2))
        transform.translate(Vector2(3, 4))
        transform.rotate(0.5)
        self.assertEqual(transform.position, Vector2(4, 6))
        self.assertIs(transform.transform.position, transform.position)
        self.assertEqual(transform.rotation, 0.5)

        velocity = VelocityComponent(Vector2(6, 8), max_speed=5)
        velocity.limit_speed()
        self.assertEqual(velocity.velocity, Vector2(3, 4))

        health = HealthComponent(max_health=10)
        health.take_damage(20)
        self.assertEqual(health.current_health, 0)
        self.assertTrue(health.is_dead)
        health.heal(4)
        self.assertEqual(health.current_health, 4)
        self.assertFalse(health.is_dead)

        tags = TagComponent('enemy')
        tags.add_tag('flying')
        tags.remove_tag('enemy')
        self.assertTrue(tags.has_tag('flying'))
        self.assertFalse(tags.has_tag('enemy'))

    def test_world_tracks_time_and_assigns_itself_to_systems(self):
        world = World()
        system = RecordingSystem()
        world.add_system(system)

        world.update(0.25)
        world.update(0.5)

        self.assertIs(system.world, world)
        self.assertEqual(world.delta_time, 0.5)
        self.assertEqual(world.total_time, 0.75)
        self.assertEqual(system.log, [('recording', 0.25), ('recording', 0.5)])

    def test_movement_system_moves_entities_and_limits_speed(self):
        world = World()
        entity = world.create_entity()
        transform = world.add_component(entity, TransformComponent())
        velocity = world.add_component(entity, VelocityComponent(Vector2(6, 8), max_speed=5))
        world.add_system(MovementSystem())

        world.update(2)

        self.assertEqual(velocity.velocity, Vector2(3, 4))
        self.assertEqual(transform.position, Vector2(6, 8))

    def test_health_system_removes_dead_entities(self):
        world = World()
        alive = world.create_entity('alive')
        dead = world.create_entity('dead')
        world.add_component(alive, HealthComponent())
        dead_health = world.add_component(dead, HealthComponent())
        dead_health.take_damage(100)
        world.add_system(HealthSystem())

        world.update(0.1)

        self.assertEqual(world.get_all_entities(), [alive])

    def test_timer_system_updates_one_shot_and_repeating_timers(self):
        calls = []
        world = World()
        one_shot_entity = world.create_entity()
        repeating_entity = world.create_entity()
        one_shot = world.add_component(
            one_shot_entity,
            TimerComponent(0.5, lambda: calls.append('once')),
        )
        repeating = world.add_component(
            repeating_entity,
            TimerComponent(0.25, lambda: calls.append('repeat'), repeat=True),
        )
        world.add_system(TimerSystem())

        world.update(0.5)
        world.update(0.5)

        self.assertEqual(calls.count('once'), 1)
        self.assertEqual(calls.count('repeat'), 2)
        self.assertTrue(one_shot.is_finished)
        self.assertFalse(repeating.is_finished)

    def test_boundary_system_can_wrap_or_clamp_positions(self):
        wrapping_world = World()
        wrapping_entity = wrapping_world.create_entity()
        wrapped = wrapping_world.add_component(
            wrapping_entity,
            TransformComponent(Vector2(-1, 101)),
        )
        wrapping_world.add_system(BoundarySystem(100, 100, wrap_around=True))
        wrapping_world.update(0)
        self.assertEqual(wrapped.position, Vector2(100, 0))

        clamping_world = World()
        clamping_entity = clamping_world.create_entity()
        clamped = clamping_world.add_component(
            clamping_entity,
            TransformComponent(Vector2(-1, 101)),
        )
        clamping_world.add_system(BoundarySystem(100, 100, wrap_around=False))
        clamping_world.update(0)
        self.assertEqual(clamped.position, Vector2(0, 100))

    def test_world_clear_removes_entities_and_stops_systems(self):
        world = World()
        component = world.add_component(world.create_entity(), RecordingComponent())
        system = RecordingSystem()
        world.add_system(system)

        world.clear()

        self.assertEqual(world.get_all_entities(), [])
        self.assertEqual(component.destroy_count, 1)
        self.assertEqual(system.stop_count, 1)


class RenderSystemTests(unittest.TestCase):
    def add_sprite(self, world, position, shape, size=None):
        entity = world.create_entity()
        world.add_component(entity, TransformComponent(position))
        world.add_component(entity, SpriteComponent(color='#123456', size=size, shape=shape))
        return entity

    def test_circle_sprite_draws_a_circle(self):
        renderer = MagicMock()
        world = World()
        world.add_system(RenderSystem(renderer))
        self.add_sprite(world, Vector2(10, 20), 'circle', Vector2(30, 30))

        world.update(0)

        renderer.draw_circle.assert_called_once_with(Vector2(10, 20), 15.0, '#123456')

    def test_triangle_sprite_draws_a_polygon_without_crashing(self):
        renderer = MagicMock()
        world = World()
        world.add_system(RenderSystem(renderer))
        self.add_sprite(world, Vector2(0, 0), 'triangle', Vector2(20, 20))

        world.update(0)

        renderer.draw_polygon.assert_called_once()
        points, color = renderer.draw_polygon.call_args.args
        self.assertEqual(color, '#123456')
        self.assertEqual(len(points), 3)

    def test_rectangle_sprite_draws_a_rectangle(self):
        renderer = MagicMock()
        world = World()
        world.add_system(RenderSystem(renderer))
        self.add_sprite(world, Vector2(5, 5), 'rectangle', Vector2(10, 10))

        world.update(0)

        renderer.draw_rectangle.assert_called_once()

    def test_invisible_sprite_is_skipped(self):
        renderer = MagicMock()
        world = World()
        world.add_system(RenderSystem(renderer))
        entity = self.add_sprite(world, Vector2.zero(), 'circle')
        world.get_component(entity, SpriteComponent).visible = False

        world.update(0)

        renderer.draw_circle.assert_not_called()


if __name__ == '__main__':
    unittest.main()
