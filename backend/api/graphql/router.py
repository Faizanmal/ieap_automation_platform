"""
GraphQL Router for FastAPI

Integrates Strawberry GraphQL with FastAPI.
"""

from strawberry.fastapi import GraphQLRouter

from .schema import get_context, schema

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphiQL IDE
    path="/graphql"
)
