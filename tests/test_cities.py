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
        "France": ("Paris", {"since": 1950}),
        "USA": ("Washington DC", {"since": 1960}),
        "India": ("New Delhi", {"since": 1970}),
        "China": ("Beijing", {"since": 1980}),
        "Russia": ("Moscow", {"since": 1990}),
    }

    def unpack(row):
        for k, v in row:
            yield k, v[0], v[1]

    await save_graph(list(unpack(capitals.items())), Country, City, CapitalRelation)
