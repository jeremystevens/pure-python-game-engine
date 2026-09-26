import unittest

import engine
from engine.ecs import Entity, World
from engine.ecs.component import Component as ECSComponent
from engine.scene.game_object import Component as GameObjectComponent


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_game_object_component_is_part_of_primary_public_api(self):
        self.assertIs(engine.Component, GameObjectComponent)
        self.assertIn('Component', engine.__all__)

    def test_ecs_types_require_explicit_experimental_imports(self):
        self.assertIsNot(ECSComponent, GameObjectComponent)
        world = World()
        entity = world.create_entity('example')
        self.assertIsInstance(entity, Entity)
        self.assertEqual(world.get_all_entities(), [entity])

        for name in ('World', 'Entity', 'EntityManager', 'System', 'SystemManager'):
            with self.subTest(name=name):
                self.assertNotIn(name, engine.__all__)
                self.assertFalse(hasattr(engine, name))


if __name__ == '__main__':
    unittest.main()
