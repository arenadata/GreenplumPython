from typing import List

import pytest

import greenplumpython as gp
from tests import db


def test_op_on_consts(db: gp.Database):
    regex_match = gp.operator("~")
    result = db.assign(is_matched=lambda: regex_match("hello", "h.*o"))
    assert len(list(result)) == 1 and next(iter(result))["is_matched"]


def test_op_index(db: gp.Database):
    import dataclasses
    import json

    @dataclasses.dataclass
    class Student:
        name: str
        courses: List[str]

    john = Student("john", ["math", "english"])
    jsonb = gp.type_("jsonb")
    rows = [(jsonb(json.dumps(john.__dict__)),)]
    student = (
        db.create_dataframe(rows=rows, column_names=["info"])
        .save_as(temp=True, column_names=["info"])
        .create_index(["info"], "gin")
    )

    db._execute("SET enable_seqscan TO False", has_results=False)
    json_contains = gp.operator("@>")
    results = student[lambda t: json_contains(t["info"], json.dumps({"name": "john"}))]._explain()
    using_index_scan = False
    for row in results:
        if "Index Scan" in row["QUERY PLAN"]:
            using_index_scan = True
            break
    assert using_index_scan


def test_op_with_schema(db: gp.Database):
    my_add = gp.operator("+")
    result = db.assign(add=lambda: my_add(1, 2))
    for row in result:
        assert row["add"] == 3
    qualified_add = gp.operator("+", "pg_catalog")
    result = db.assign(add=lambda: qualified_add(1, 2))
    for row in result:
        assert row["add"] == 3


# FIXME : Add test for unary operator
