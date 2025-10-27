"""
Continuous Data Generation Module for Asana.

This module provides realistic, ongoing data generation for Asana workspaces
with industry-specific content powered by Claude AI.
"""

__version__ = "1.0.0"
__author__ = "Asana Data Generator Team"

from .service import ContinuousService
from .state_manager import StateManager
from .llm_generator import LLMGenerator
from .asana_client import AsanaClient, AsanaClientPool
from .scheduler import ActivityScheduler, ActivityType

__all__ = [
    "ContinuousService",
    "StateManager",
    "LLMGenerator",
    "AsanaClient",
    "AsanaClientPool",
    "ActivityScheduler",
    "ActivityType",
]
