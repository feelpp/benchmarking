from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode
import pytest


@pytest.mark.parametrize("dictTree, expected", [
    ({}, []),  # Empty tree case
    ({"A": "B"}, [["A", "B"]]),  # Single key-value pair
    ({"A": {"B": "C"}}, [["A", "B", "C"]]),  # Simple nested case
    ({"A": {"B": "C", "D": "E"}}, [["A", "B", "C"], ["A", "D", "E"]]),  # Two branches at second level
    ({"A": {"B": {"C": "D"}}}, [["A", "B", "C", "D"]]),  # Deeply nested single path
    ({"A": {"B": "C"}, "D": {"E": "F"}}, [["A", "B", "C"], ["D", "E", "F"]]),  # Multiple top-level keys
    ({"A": {"B": {"C": "D", "E": "F"}, "G": "H"}},
     [["A", "B", "C", "D"], ["A", "B", "E", "F"], ["A", "G", "H"]])  # Complex case with mixed depths
])
def test_treeToList(dictTree,expected):
    assert TreeUtils.dictTreeToLists(dictTree) == expected



@pytest.mark.parametrize("a, b, expected", [
    ( {"x": 1}, {"y": 2}, {"x": 1, "y": 2} ), # --- Basic independent keys ---
    ( {"x": 1}, {"x": 99}, {"x": 99} ),# --- Scalar overwrite ---
    ( {"a": {"b": 1}}, {"a": {"c": 2}}, {"a": {"b": 1, "c": 2}} ), # --- Simple nested merge ---
    ( {"a": {"b": 1}}, {"a": 42}, {"a": 42} ),# --- Nested overwrite entire subtree (b not a dict) ---
    ( {"a": {"b": {"c": 1}}}, {"a": {"b": {"d": 2}}}, {"a": {"b": {"c": 1, "d": 2}}} ), # --- Deep recursive merge ---
    ( {"a": {"b": 1}}, {"a": {"b": {"bad": "val"}}}, {"a": {"b": {"bad": "val"}}} ), # --- Type conflict: overwrite when a[key] not dict ---
    ( # --- Multiple levels, several merges + new keys ---
        {"x": 1, "a": {"b": 2, "d": {"e": 5}}}, {"a": {"c": 3, "d": {"f": 6}}, "y": 10},
        {"x": 1, "y": 10, "a": { "b": 2, "c": 3, "d": {"e": 5, "f": 6}  } },
    ),
])
def test_mergeDicts(a, b, expected):
    assert TreeUtils.mergeDicts(a, b) == expected


def make_tree():
    #         root
    #         /   |   \
    #     A    B    C
    #     / \        \
    #     A1 A2        C1

    root = GraphNode("root", None)

    A = GraphNode("A", None)
    A1 = GraphNode("A1", None)
    A2 = GraphNode("A2", None)
    A.addChild(A1)
    A.addChild(A2)

    B = GraphNode("B", None)

    C = GraphNode("C", None)
    C1 = GraphNode("C1", None)
    C.addChild(C1)

    root.addChild(A)
    root.addChild(B)
    root.addChild(C)
    return root


@pytest.mark.parametrize(
    "perm, permuteLeaves, expected_paths",
    [

        # --------------------------------------------------------------
        # 1. Identity permutation: nothing changes
        # --------------------------------------------------------------
        ( [0, 1], False, [
            ["root", "A", "A1"],
            ["root", "A", "A2"],
            ["root", "B"],
            ["root", "C", "C1"],
        ]),

        # --------------------------------------------------------------
        # 2. Swap first two internal levels
        #    perm=[1,0] applied on paths below root
        # --------------------------------------------------------------
        ( [1, 0], False, [
            ["root", "A", "A1"],   # A has only 1 internal level -> unchanged
            ["root", "A", "A2"],
            ["root", "B"],         # leaf -> unchanged
            ["root", "C", "C1"],   # only 1 internal level -> unchanged
        ]),

        # --------------------------------------------------------------
        # 3. Reverse with permuteLeaves=True
        # --------------------------------------------------------------
        ( [1, 0], True, [
            ["root", "A1", "A"],   # reversed
            ["root", "A2", "A"],
            ["root", "B"],         # leaf stays as is
            ["root", "C1", "C"],   # reversed
        ]),

        # --------------------------------------------------------------
        # 4. Perm index exceeds path length -> skipped
        # --------------------------------------------------------------
        ( [2, 1, 0], False, [
            ["root", "A", "A1"],  # too short -> effectively identity
            ["root", "A", "A2"],
            ["root", "B"],
            ["root", "C", "C1"],
        ]),

        # --------------------------------------------------------------
        # 5. PermuteLeaves=True on mixed-depth paths
        # --------------------------------------------------------------
        ( [0], True, [ ["root", "A"], ["root", "B"], ["root", "C"], ] ),
    ]
)
def test_permuteTree(perm, permuteLeaves, expected_paths):

    root = make_tree()
    new_root = TreeUtils.permuteTree(root, perm, permuteLeaves)

    def collect(node, path, out):
        path = path + [node.id]
        if node.isLeaf():
            out.append(path)
            return
        for c in node.children:
            collect(c, path, out)

    got_paths = []
    collect(new_root, [], got_paths)

    # Sort to ignore ordering of siblings for comparison
    norm = lambda lst: sorted(["/".join(p) for p in lst])

    assert norm(got_paths) == norm(expected_paths)
