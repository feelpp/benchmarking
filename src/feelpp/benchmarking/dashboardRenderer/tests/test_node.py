from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode
from feelpp.benchmarking.dashboardRenderer.component.leaf import LeafComponent
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateDataFile

import pytest

class MockView:
    def __init__(self,name = ""):
        self.name = name
        self.template_data = {"test":"template_data"}
    def clone(self):
        return MockView(f"Cloned {self.name}")
    def updateTemplateData(self,data):
        self.template_data.update(data)

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



def test_clone():
    view_a = MockView("MainView")
    a = GraphNode("A", view_a)
    a.setRepository(GraphNode("Repo", None))

    b = a.clone()

    # Assert basic cloning
    assert b.id == "A"
    assert b.repository.id == "Repo"
    assert b is not a

    # Assert View cloning
    assert b.view is not view_a
    assert b.view.name == "Cloned MainView"
    assert b.view.template_data == view_a.template_data # Same content, different object
    assert isinstance(b.view, MockView)

    # Assert children/parents are not cloned
    assert b.children == set()
    assert b.parents == set()

    # Case 2: Node without a View (original test case, but now explicit)
    c = GraphNode("C", None)
    d = c.clone()
    assert d.id == "C"
    assert d.view is None
    assert d is not c


def test_traverse():
    root = GraphNode("R", None)
    a1 = GraphNode("A1", None)
    a2 = GraphNode("A2", None)
    b1 = GraphNode("B1", None)
    b2 = GraphNode("B2", None)

    root.addChild(a1)
    root.addChild(a2)
    a1.addChild(b1)
    a1.addChild(b2)

    visited_nodes = {} # Stores {node_id: level}

    def visitor_fn(node: GraphNode, level: int) -> None:
        visited_nodes[node.id] = level

    root.traverse(visitor_fn)

    # Check that all 5 nodes were visited
    assert len(visited_nodes) == 5
    assert "R" in visited_nodes
    assert "A1" in visited_nodes
    assert "A2" in visited_nodes
    assert "B1" in visited_nodes
    assert "B2" in visited_nodes

    # Check the levels
    assert visited_nodes["R"] == 0
    assert visited_nodes["A1"] == 1
    assert visited_nodes["A2"] == 1
    assert visited_nodes["B1"] == 2
    assert visited_nodes["B2"] == 2



def test_upstreamViewData_aggregation():
    """
    Tests the recursive upstream aggregation of view data, ensuring all nodes
    are touched and data flows from leaves to root.
    """
    # Setup node structure and mock views
    # R (Root) -> A1 -> B1 (Leaf)
    # R (Root) -> A2 (Leaf)
    # Views track their own IDs for verification
    view_r = MockView("R")
    view_a1 = MockView("A1")
    view_a2 = MockView("A2")
    view_b1 = MockView("B1")

    r = GraphNode("R", view_r)
    a1 = GraphNode("A1", view_a1, {r})
    a2 = GraphNode("A2", view_a2, {r})
    b1 = GraphNode("B1", view_b1, {a1})

    # The aggregator function sums up the counts from children and adds 1 for itself
    def aggregator(node_id: str, repo_id: str, template_data: dict, child_results: list) -> dict:
        count = 1 + sum(cr.get("count", 0) for cr in child_results)
        return {"id": node_id, "count": count}

    final_result = r.upstreamViewData(aggregator)

    # 1. Check the final result at the root (R)
    # B1 (1) -> A1 (1+1=2)
    # A2 (1)
    # R (1 + 2 + 1 = 4)
    assert final_result["id"] == "R"
    assert final_result["count"] == 4

    # 2. Check that the "aggregated" data was stored on every node's view
    assert r.view.template_data["aggregated"]["count"] == 4
    assert a1.view.template_data["aggregated"]["count"] == 2
    assert a2.view.template_data["aggregated"]["count"] == 1
    assert b1.view.template_data["aggregated"]["count"] == 1

def test_addParent():
    """Tests adding a parent and ensuring bidirectional linkage and idempotency."""
    a = GraphNode("A", None)
    b = GraphNode("B", None)

    # 1. Add B as parent to A
    a.addParent(b)

    assert b in a.parents
    assert a in b.children

    # 2. Ensure calling again is idempotent (no duplicates)
    a.addParent(b)
    assert len(a.parents) == 1
    assert len(b.children) == 1

    # 3. Add a different parent C
    c = GraphNode("C", None)
    a.addParent(c)

    assert c in a.parents
    assert a in c.children
    assert len(a.parents) == 2
    assert len(b.children) == 1
    assert len(c.children) == 1


def test_leafcomponentInit():
    """Tests ID construction and repository assignment in LeafComponent.__init__."""
    repo = GraphNode("TestRepo",None)
    view = MockView("LeafView")
    parent_ids = ["parentA", "parentB"]
    item_name = "item_001"

    leaf = LeafComponent(item_name, repo, parent_ids, view)

    # 1. Check ID construction
    expected_id = "parentA-parentB-item_001"
    assert leaf.id == expected_id

    # 2. Check repository assignment
    assert leaf.repository is repo

    # 3. Check specific attributes
    assert leaf.item_name == item_name
    assert leaf.parent_ids == parent_ids
    assert leaf.view is view

def test_leafcomponentClone():
    """Tests that calling clone on LeafComponent raises a RuntimeError."""
    repo = GraphNode("TestRepo",None)
    view = MockView()
    leaf = LeafComponent("item", repo, ["p"], view)

    with pytest.raises(RuntimeError) as excinfo:
        leaf.clone()

    assert "Leaf component cannot be cloned" in str(excinfo.value)

def test_leafcomponent_getPermParentIdsStr():
    """
    Tests the logic for compiling all unique hierarchical parent ID paths
    as a comma-separated string.
    """
    # Structure: Root -> A1 -> B1 (Leaf)
    #            Root -> A2 -> B1 (Leaf - multi-parent scenario is covered by GraphNode's structure)
    root = GraphNode("Root", None)
    a1 = GraphNode("A1", None, {root})
    a2 = GraphNode("A2", None, {root}) # A2 also linked to root

    repo = GraphNode("R",None)
    view = MockView()

    # Create the leaf and explicitly link it to both parents (A1 and A2)
    # LeafComponent's constructor only takes a parent_ids list, which is for its ID construction,
    # but the parents set is updated via the GraphNode constructor.
    leaf_id_list = ["A1", "B1"] # ID will be A1-B1-item_L
    leaf = LeafComponent("item_L", repo, leaf_id_list, view)

    # Manually set up the GraphNode links for multi-parent testing
    leaf.parents = {a1, a2} # Link to both A1 and A2
    a1.children.add(leaf)
    a2.children.add(leaf)

    # Path 1 (via A1): [L, A1, Root] -> Reversed parents: [A1, Root] -> 'A1-Root'
    # Path 2 (via A2): [L, A2, Root] -> Reversed parents: [A2, Root] -> 'A2-Root'

    parent_id_str = leaf.getPermParentIdsStr()

    # The result should contain all unique parent paths, separated by a comma.
    # The order of paths depends on the set iteration, so we check for sets of strings.
    paths = set(parent_id_str.split(','))

    assert paths == {"Root-A1", "Root-A2"}


def test_leafcomponent_patchTemplateInfo_no_save():
    """Tests that patchTemplateInfo updates data correctly when save=False."""
    view = MockView()
    leaf = LeafComponent("item", GraphNode("R",None), ["p"], view)

    patch_data = {"test_key": 123, "nested": {"a": "b"}}
    prefix = "meta"

    leaf.patchTemplateInfo(patch_data, prefix, save=False)

    assert view.template_data["meta"] == patch_data
    # Ensure no file operations occurred (implicitly, as we aren't mocking open/json.dump)