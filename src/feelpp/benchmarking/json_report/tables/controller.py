import pandas as pd
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import Table, FilterCondition, SortInstruction, GroupBy, Pivot

class Controller:
    def __init__(self, data: pd.DataFrame, table_config: Table) -> None:
        """
        data: a pandas DataFrame containing the dataset
        table_config: a Table Pydantic model defining filtering, grouping, pivot, etc.
        """
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = table_config
        self.column_order = self.config.column_order

    def generate(self) -> pd.DataFrame:
        """Generate a Pandas DataFrame according to the Table config."""
        if self.data.empty:
            return self.data

        df = self.data.copy()

        df = self._applyFilter(df)

        df = self._selectColumns(df)

        df = self._computeColumns(df)

        if self.config.pivot:
            df = self._pivot(df)
        elif self.config.group_by:
            df = self._groupAndAggregate(df)

        df = self._sort(df)

        df = self._format(df)

        df = self._reorderColumns(df)

        df = self._renameColumns(df)

        return df


    def getColsAlignment(self) -> str:
        """
        Generate the AsciiDoc cols="..." string based on column_align in style.
        Defaults to 'left' if not specified.
        Returns a string like: "c,l,r,l,r"
        """
        align_map = {"left": "<", "center": "^", "right": ">"}

        cols = []
        column_align = self.config.style.column_align
        column_width = self.config.style.column_width
        for col in self.column_order:
            a = column_align.get(col)
            w = column_width.get(col,3)
            cols.append(f"{align_map.get(a,'<')}{w}")

        return ",".join(cols)

    # -----------------------------
    # Private helper methods
    # -----------------------------

    def _applyFilter(self, df: pd.DataFrame) -> pd.DataFrame:
        for f in self.config.filter:
            col, op, val = f.column, f.op, f.value
            if op == "==":
                df = df[df[col] == val]
            elif op == "!=":
                df = df[df[col] != val]
            elif op == ">":
                df = df[df[col] > val]
            elif op == "<":
                df = df[df[col] < val]
            elif op == ">=":
                df = df[df[col] >= val]
            elif op == "<=":
                df = df[df[col] <= val]
            elif op == "in":
                df = df[df[col].isin(val)]
            elif op == "not in":
                df = df[~df[col].isin(val)]
            else:
                raise ValueError(f"Unknown filter operator: {op}")
        return df

    def _selectColumns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.columns:
            df = df[self.config.columns]
        return df

    def _renameColumns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.rename:
            df = df.rename(columns=self.config.rename)
        return df

    def _groupAndAggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        gb: GroupBy = self.config.group_by

        agg_cfg = gb.agg
        if isinstance(agg_cfg, str):
            cols_to_agg = [c for c in df.columns if c not in gb.columns]
            agg_cfg = {col: agg_cfg for col in cols_to_agg}

        return df.groupby(gb.columns, dropna=False, as_index=False).agg(agg_cfg)

    def _pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        pv: Pivot = self.config.pivot
        return df.pivot_table(
            index=pv.index,
            columns=pv.columns,
            values=pv.values,
            aggfunc=pv.agg,
            dropna=False
        ).reset_index()

    def _sort(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.sort:
            cols = [s.column for s in self.config.sort]
            asc = [s.ascending for s in self.config.sort]
            df = df.sort_values(by=cols, ascending=asc)
        return df

    def _format(self, df: pd.DataFrame) -> pd.DataFrame:
        for col, fmt in self.config.format.items():
            if col in df.columns:
                if isinstance(fmt, dict):
                    df[col] = df[col].apply(lambda x: fmt.get(str(x), x))
                else:
                    try:
                        df[col] = df[col].apply(lambda x: fmt % x)
                    except Exception:
                        df[col] = df[col].astype(str)
        return df


    def _reorderColumns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.column_order:
            order = [c for c in self.config.column_order if c in df.columns]
            df = df[order]
        else:
            self.column_order = df.columns.tolist()
        return df

    def _computeColumns(self, df:pd.DataFrame) -> pd.DataFrame:
        if not self.config.computed_columns:
            return df

        for newcol, expr in self.config.computed_columns.items():
            df[newcol] = df.apply(lambda row: eval(expr,{},dict(row=row)), axis=1)
        return df