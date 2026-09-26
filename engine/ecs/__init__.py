"""Experimental Entity Component System implementation.

GameObject components are the engine's primary supported architecture. ECS APIs
remain available through this explicit subpackage for experiments and demos.
"""

from .entity import Entity, EntityManager
from .component import Component
from .system import System, SystemManager
from .world import World

__all__ = ['Entity', 'EntityManager', 'Component', 'System', 'SystemManager', 'World']
