from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
import pytest

@pytest.mark.parametrize("tree, expected", [
    ({}, []),  # Empty tree case
    ({"A": "B"}, [["A", "B"]]),  # Single key-value pair
    ({"A": {"B": "C"}}, [["A", "B", "C"]]),  # Simple nested case
    ({"A": {"B": "C", "D": "E"}}, [["A", "B", "C"], ["A", "D", "E"]]),  # Two branches at second level
    ({"A": {"B": {"C": "D"}}}, [["A", "B", "C", "D"]]),  # Deeply nested single path
    ({"A": {"B": "C"}, "D": {"E": "F"}}, [["A", "B", "C"], ["D", "E", "F"]]),  # Multiple top-level keys
    ({"A": {"B": {"C": "D", "E": "F"}, "G": "H"}},
     [["A", "B", "C", "D"], ["A", "B", "E", "F"], ["A", "G", "H"]])  # Complex case with mixed depths
])
def test_treeToList(tree,expected):
    tree_list = TreeUtils.treeToLists(tree)
    assert tree_list == expected



@pytest.mark.parametrize("tree, permutation, expected", [
    ({"A": {"B": "C"}}, [0, 1], {"A": {"B": "C"}}), # Basic case: No permutation (identity)
    ({"A": {"B": "C"}}, [1, 0], {"B": {"A": "C"}}), # Swap two levels
    ({"A": {"B": {"C": "D"}}}, [1, 0, 2], {"B": {"A": {"C": "D"}}}), # Three levels, swapping first and second
    ({"A": {"B": {"C": "D", "E": "F"}}}, [1, 0, 2], {"B": {"A": {"C": "D", "E": "F"}}}), # More complex tree with swaps
    ({"A": {"B": {"C": "D"}}}, [2, 1, 0], {"C": {"B": {"A": "D"}}}), # Three levels, swapping first and third
    ({
        "A": {"B": {"C": "D", "E": "F"}},
        "X": {"Y": {"Z": "W"}}
    }, [1, 0, 2],
    {
        "B": {"A": {"C": "D", "E": "F"}},
        "Y": {"X": {"Z": "W"}}
    })  # Multiple branches, swapping levels
])
def test_permuteTreeLevels(tree, permutation, expected):
    """Test that permuteTreeLevels correctly rearranges tree levels."""
    result = TreeUtils.permuteTreeLevels(tree, permutation)
    assert result == expected

@pytest.mark.parametrize(("tree","permutation", "error"), [
    ({"A": {"B": "C"}}, [0], ValueError),  # Invalid permutation length
    ({"A": {"B": {"C": "D"}}}, [0, 1], ValueError),  # Missing level in permutation
    ({"A": {"B": "C"}}, [2, 1], IndexError),  # Out of range permutation
])
def test_permuteTreeLevels_errors(tree, permutation, error):
    """Test that permuteTreeLevels raises error on incorrect permutations."""
    with pytest.raises(error):
        TreeUtils.permuteTreeLevels(tree, permutation)