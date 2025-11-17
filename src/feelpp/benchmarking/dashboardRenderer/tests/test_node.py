from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode
import pytest


def test_constructorLinks():
    a = GraphNode("A", None)
    b = GraphNode("B", None, {a})

    assert b in a.children
    assert a in b.parents

def test_addChild():
    a = GraphNode("A", None)
    b1 = GraphNode("B", None)
    b2 = GraphNode("B", None)

    g = GraphNode("G", None)
    b2.addChild(g)

    a.addChild(b1)
    a.addChild(b2)

    assert len(a.children) == 1   # merged
    merged_b = next(iter(a.children))
    assert merged_b.id == "B"
    assert g in merged_b.children   # grandchildren merged

def test_isRoot_isLeaf():
    a = GraphNode("A", None)
    b = GraphNode("B", None, {a})

    assert a.isRoot()
    assert not b.isRoot()

    assert not a.isLeaf()
    assert b.isLeaf()

def test_clone():
    a = GraphNode("A", None)
    b = a.clone()

    assert b.id == "A"
    assert b.children == set()
    assert b.parents == set()
    assert b.repository == a.repository
    assert b is not a

def test_getChild():
    a = GraphNode("A", None)
    b = GraphNode("B", None)
    a.addChild(b)

    assert a.get("B") is b
    assert a.get("X") is None


def test_unlink():
    a = GraphNode("A", None)
    b = GraphNode("B", None, {a})
    c = GraphNode("C", None, {b})

    a.unlink()

    assert a.children == set()
    assert b.parents == set()
    assert c.parents == set()

def test_getLeaves():
    root = GraphNode("root", None)
    a = GraphNode("A", None, {root})
    b = GraphNode("B", None, {root})
    c = GraphNode("C", None, {a})

    leaves = root.getLeaves()

    assert set(n.id for n in leaves) == {"B", "C"}

def test_getPathToRoot():
    root = GraphNode("root", None)
    a = GraphNode("A", None, {root})
    b = GraphNode("B", None, {a})

    paths = b.getPathToRoot()

    assert len(paths) == 1
    assert [n.id for n in paths[0]] == ["B", "A", "root"]
