import pytest
from pydantic import ValidationError
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import Table, FilterCondition, SortInstruction, GroupBy, Pivot


class TestTableSchema:

    # ------------------------------------------------------------------
    # Defaults / empty initialization
    # ------------------------------------------------------------------
    def test_empty_table_defaults(self):
        t = Table()
        assert t.columns == []
        assert t.computed_columns == {}
        assert t.rename == {}
        assert t.filter == []
        assert t.sort == []
        assert t.group_by is None
        assert t.pivot is None
        assert t.format == {}
        assert t.column_order == []

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "filters",
        [
            [FilterCondition(column="x", op="==", value=10)],
            [
                FilterCondition(column="y", op=">", value=5),
                FilterCondition(column="z", op="in", value=[1, 2, 3])
            ]
        ],
    )
    def test_table_with_filters(self, filters):
        t = Table(filter=filters)
        assert t.filter == filters

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "sort_instructions",
        [
            [SortInstruction(column="x")],
            [SortInstruction(column="x", ascending=False), SortInstruction(column="y")],
        ]
    )
    def test_table_with_sorting(self, sort_instructions):
        t = Table(sort=sort_instructions)
        assert t.sort == sort_instructions

    # ------------------------------------------------------------------
    # Computed columns and rename
    # ------------------------------------------------------------------
    def test_table_computed_and_rename(self):
        t = Table(computed_columns={"c1": "a + b"}, rename={"a": "alpha"})
        assert t.computed_columns == {"c1": "a + b"}
        assert t.rename == {"a": "alpha"}

    # ------------------------------------------------------------------
    # Group by valid
    # ------------------------------------------------------------------
    def test_table_group_by_valid(self):
        gb = GroupBy(columns=["col1"], agg={"val": "sum"})
        t = Table(group_by=gb)
        assert t.group_by == gb

    # ------------------------------------------------------------------
    # Pivot valid
    # ------------------------------------------------------------------
    def test_table_pivot_valid(self):
        pv = Pivot(index=["row"], columns=["col"], values="val", agg="sum")
        t = Table(pivot=pv)
        assert t.pivot == pv

    # ------------------------------------------------------------------
    # Exclusivity errors: group_by + pivot
    # ------------------------------------------------------------------
    def test_table_group_by_and_pivot_raises(self):
        gb = GroupBy(columns=["col1"], agg={"val": "sum"})
        pv = Pivot(index=["row"], columns=["col"], values="val", agg="sum")
        with pytest.raises(ValueError, match="Cannot use both 'group_by' and 'pivot'"):
            Table(group_by=gb, pivot=pv)

    # ------------------------------------------------------------------
    # GroupBy missing agg
    # ------------------------------------------------------------------
    def test_table_group_by_missing_agg_raises(self):
        gb = GroupBy(columns=["col1"], agg={})
        with pytest.raises(ValueError, match="'group_by' requires an 'agg' mapping"):
            Table(group_by=gb)

    # ------------------------------------------------------------------
    # Pivot with sort raises
    # ------------------------------------------------------------------
    def test_table_pivot_with_sort_raises(self):
        pv = Pivot(index=["row"], columns=["col"], values="val", agg="sum")
        sort_instr = [SortInstruction(column="val")]
        with pytest.raises(ValueError, match="Sorting a pivoted table is ambiguous"):
            Table(pivot=pv, sort=sort_instr)
