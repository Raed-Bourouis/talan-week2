"""
F360 – Neo4j Connection Manager
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import get_settings

settings = get_settings()

_driver: AsyncDriver | None = None


async def get_neo4j_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


async def close_neo4j_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


@asynccontextmanager
async def neo4j_session():
    """Yields an async Neo4j session."""
    driver = await get_neo4j_driver()
    async with driver.session() as session:
        yield session
