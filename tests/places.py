from dataclasses import field

from pgraph import graph, property


@graph
class Country:
    name: str = field(default=None)


@graph
class City:
    name: str = field(default=None)


@property
class CapitalRelation:
    since: int = field(default=0)
