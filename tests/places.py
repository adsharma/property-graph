from pgraph import graph, property


@graph
class Country:
    name: str


@graph
class City:
    name: str


@property
class CapitalRelation:
    since: int = 1950
