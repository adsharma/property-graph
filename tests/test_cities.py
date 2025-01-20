import pytest
from places import CapitalRelation, City, Country
from sqlmodel import SQLModel

from pgraph import save_graph
from pgraph.database import engine


def init_edge_types():
    CapitalRelation()


pytest_plugins = ("pytest_asyncio",)
SQLModel.metadata.create_all(engine)
init_edge_types()


@pytest.mark.asyncio
async def test_cities():
    capitals = {
        "France": "Paris",
        "USA": "Washington DC",
        "India": "New Delhi",
        "China": "Beijing",
        "Russia": "Moscow",
    }
    await save_graph(capitals.items(), Country, City, CapitalRelation)
