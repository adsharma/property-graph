from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List

from fquery.sqlmodel import SQL_PK, model
from sqlmodel import SQLModel, select

from pgraph.database import Database, allocate_ids


@model(global_id=True)
@dataclass
class ObjectType:
    name: str
    id: int | None = None


@model(global_id=True)
@dataclass
class PropertyType:
    name: str
    id: int | None = None


@model(table_name="nodes")
@dataclass(kw_only=True)
class GraphBase:
    id: int | None = field(default=None)
    ntype: int = field(default=0)
    properties: Dict = field(default_factory=lambda: {})

    def create_object_type_relation(self, derived):
        if not hasattr(derived, "TYPE"):
            self.create_object_type(derived)
        self.ntype = self.TYPE.id

    @classmethod
    def create_object_type(cls, derived):
        cls = derived
        # check if ObjectType exists in db
        db = Database().db
        obj_sqlmodel = ObjectType(cls.__name__).sqlmodel()
        ObjectTypeSQLModel = obj_sqlmodel.__class__
        statement = select(ObjectTypeSQLModel).where(
            ObjectTypeSQLModel.name == cls.__name__
        )
        result = db.exec(statement).first()
        if result is None:
            with db as session:
                session.add(obj_sqlmodel)
                session.commit()
                session.refresh(obj_sqlmodel)
        else:
            obj_sqlmodel = result
        cls.TYPE = ObjectType(obj_sqlmodel.name, obj_sqlmodel.id)

    def __post_init__(self):
        self.properties = {}
        self.create_object_type_relation(self.__class__)


@dataclass(kw_only=True)
class PropertyBase:
    rtype: int = field(default=0)
    properties: Dict = field(default_factory=lambda: {})

    @classmethod
    def create_property_type(cls):
        # check if PropertyType exists in db
        db = Database().db
        prop_sqlmodel = PropertyType(cls.__name__).sqlmodel()
        PropertyTypeSQLModel = prop_sqlmodel.__class__
        statement = select(PropertyTypeSQLModel).where(
            PropertyTypeSQLModel.name == cls.__name__
        )
        result = db.exec(statement).first()
        if result is None:
            with db as session:
                session.add(prop_sqlmodel)
                session.commit()
                session.refresh(prop_sqlmodel)
        else:
            prop_sqlmodel = result
        cls.TYPE = PropertyType(prop_sqlmodel.name, prop_sqlmodel.id)

    def __post_init__(self):
        self.properties = {}
        if not hasattr(self.__class__, "TYPE"):
            self.create_property_type()
        self.rtype = self.TYPE.id


def inject_base(cls):
    extras = {"__post_init__": GraphBase.__post_init__}
    cls = type(cls.__name__, (GraphBase,), {**cls.__dict__, **extras})
    cls.create_object_type = GraphBase.create_object_type
    cls.create_object_type_relation = GraphBase.create_object_type_relation
    return cls


def inject_property_base(cls):
    extras = {"__post_init__": PropertyBase.__post_init__}
    return type(cls.__name__, (PropertyBase,), {**cls.__dict__, **extras})


def graph(cls):
    return inject_base(cls)


def property(cls):
    return inject_property_base(cls)


INFINITY_DATE = date.max


@model(global_id=True)
@dataclass
class Relation:
    src: int = field(**SQL_PK)
    rtype: int = field(**SQL_PK)
    dst: int = field(**SQL_PK)
    start: date = field(default_factory=date.today)
    end: date | None = field(default_factory=lambda: INFINITY_DATE)
    properties: Dict = field(default_factory=lambda: {})
    probability: float = field(default_factory=lambda: 1.0)
    viewpoint: int | None = 0


async def save_graph(
    rows: List, left_model: SQLModel, right_model: SQLModel, relation_class: Relation
) -> int:
    ids = allocate_ids(2 * len(rows))

    with Database().db as session:
        for left, right, *_ in rows:
            left_obj = left_model().sqlmodel()
            right_obj = right_model().sqlmodel()
            # Consider setting a strongly typed field and then serializing to the property dict in the future.
            left_obj.properties["name"] = left
            right_obj.properties["name"] = right
            left_obj.id = ids.pop(0)
            right_obj.id = ids.pop(0)
            session.add(left_obj)
            session.add(right_obj)
            typed_relation = relation_class()
            relation = Relation(
                src=left_obj.id,
                rtype=typed_relation.TYPE.id,
                dst=right_obj.id,
            )
            relation.properties["since"] = typed_relation.since
            session.add(relation.sqlmodel())
        session.commit()
    return len(rows)


# Unlike save_graph, this saves only objects of a given type. Relations to be added later
async def save_objs(rows: List, left_model: SQLModel, refresh=False) -> List[SQLModel]:
    ids = allocate_ids(len(rows))
    objs = []

    with Database().db as session:
        for left in rows:
            left_obj = left_model(*left).sqlmodel()
            left_obj.id = ids.pop(0)
            objs.append(left_obj)
            session.add(left_obj)
        session.commit()
        if refresh:
            [session.refresh(o) for o in objs]
    return objs


async def save_graph_prob(
    left_id: int, rows: List, right_model: SQLModel, relation_class: Relation
) -> int:
    ids = allocate_ids(len(rows))

    with Database().db as session:
        for right, prob, *_ in rows:
            right_obj = right_model(right).sqlmodel()
            right_obj.id = ids.pop(0)
            session.add(right_obj)
            relation = Relation(
                src=left_id,
                rtype=relation_class.TYPE.id,
                dst=right_obj.id,
                probability=prob,
            )
            session.add(relation.sqlmodel())
        session.commit()
    return len(rows)
