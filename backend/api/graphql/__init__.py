"""
GraphQL API Layer

Modern GraphQL interface for flexible data fetching and real-time subscriptions.
"""

from .router import graphql_router
from .schema import get_context, schema

__all__ = ["get_context", "graphql_router", "schema"]
