#!/usr/bin/env python3
"""
Service abstraction layer for continuous data generation.
Supports multiple platform types (Asana, Okta, future platforms).
"""

from continuous.services.base_service import BaseService
from continuous.services.asana_service import AsanaService

__all__ = [
    'BaseService',
    'AsanaService',
]
