#!/usr/bin/env python3
"""
Connection abstraction layer for data generator.
Supports multiple platform types (Asana, Okta, future platforms).
"""

from continuous.connections.base_connection import (
    BaseConnection,
    BaseClientPool,
    ConnectionError,
    RateLimitError
)
from continuous.connections.asana_connection import (
    AsanaConnection,
    AsanaClientPool
)
from continuous.connections.okta_connection import (
    OktaConnection,
    OktaClientPool
)

__all__ = [
    'BaseConnection',
    'BaseClientPool',
    'ConnectionError',
    'RateLimitError',
    'AsanaConnection',
    'AsanaClientPool',
    'OktaConnection',
    'OktaClientPool',
]
