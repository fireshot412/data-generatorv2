"""
Continuous Data Generation Module.

This module provides realistic, ongoing data generation for multiple platforms
(Asana, Okta, etc.) with industry-specific content powered by Claude AI.
"""

__version__ = "2.0.0"
__author__ = "Data Generator Team"

# New modular structure
from .services.asana_service import AsanaService, ContinuousService
from .connections.asana_connection import AsanaConnection, AsanaClientPool
from .state_manager import StateManager
from .llm_generator import LLMGenerator
from .scheduler import ActivityScheduler, ActivityType

__all__ = [
    # Services
    "AsanaService",
    "ContinuousService",  # Backwards compatibility
    # Connections
    "AsanaConnection",
    "AsanaClientPool",
    # Core components
    "StateManager",
    "LLMGenerator",
    "ActivityScheduler",
    "ActivityType",
]
