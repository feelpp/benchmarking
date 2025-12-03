import pandas as pd
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import TableLayout, TableStyle

class Controller:
    def __init__(self, data: pd.DataFrame, table_layout: TableLayout, table_style:TableStyle) -> None:
        """
        data: a pandas DataFrame containing the dataset
        table_layout: a Table Pydantic model defining ordering, renaming, and other aesthetical operations
        """
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.style = table_style
        self.layout = table_layout

    def generate(self) -> pd.DataFrame:
        """Generate a Pandas DataFrame according to the Table config."""
        if self.data.empty:
            return self.data

        df = self.data.copy()

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
        column_align = self.style.column_align
        column_width = self.style.column_width
        for col in self.layout.column_order:
            a = column_align.get(col)
            w = column_width.get(col,3)
            cols.append(f"{align_map.get(a,'<')}{w}")

        return ",".join(cols)

    def _renameColumns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.layout.rename:
            df = df.rename(columns=self.layout.rename)
        return df



    def _reorderColumns(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.layout.column_order:
            order = [c for c in self.layout.column_order if c in df.columns]
            df = df[order]
        else:
            self.layout.column_order = df.columns.tolist()
        return df
