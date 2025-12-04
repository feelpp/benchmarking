from typing import Union, Type, List, Dict
from feelpp.benchmarking.json_report.schemas.dataRefs import DataFile, InlineTable, InlineRaw, InlineObject,DataTable,DataObject,DataRaw,DataField, Preprocessor
from feelpp.benchmarking.json_report.schemas.dataRefs import Pivot, GroupBy, SortInstruction, FilterCondition
import pandas as pd
import json


class DataFieldParser:
    def __init__(self,data_field: Union[DataTable,DataObject,DataRaw]):
        self.data_field = data_field

    def load(self):
        raise NotImplementedError("Pure virtual function, must be implemented in child class")

    def process(self, filedata: Union[pd.DataFrame,dict,str]):
        if self.data_field.preprocessor:
            filedata = self.data_field.preprocessor.apply(filedata)
        return filedata


class DataTableParser(DataFieldParser):
    def load(self) -> pd.DataFrame:
        source = self.data_field.source
        if isinstance(source,DataFile):
            with open( source.filepath, "r" ) as f:
                if source.format == "csv":
                    filedata =  pd.read_csv(f)
                elif source.format == "json":
                    filedata = json.load(f)
                    if not self.data_field.preprocessor:
                        self.data_field.preprocessor = Preprocessor.model_construct(module=pd,function=pd.DataFrame.from_dict)
                else:
                    raise NotImplementedError(f"Cannot create DataTable from {source.format} files")
        elif isinstance(source,InlineTable):
            filedata = source.columns
            if not self.data_field.preprocessor:
                self.data_field.preprocessor = Preprocessor.model_construct(module=pd,function=lambda x : pd.DataFrame.from_dict({c.name:c.values for c in source.columns}))
        else:
            raise NotImplementedError(f"Cannot create a DataTable from  type {type(source)}")

        filedata = self.process(filedata)
        return filedata


    def process(self,filedata: Union[pd.DataFrame,dict,str]):
        filedata = super().process(filedata)
        opts = self.data_field.table_options
        if isinstance(filedata, pd.DataFrame):
            filedata = self._applyFilter(opts.filter,filedata)
            filedata = self._computeColumns(opts.computed_columns,filedata)
            if opts.pivot:
                filedata = self._pivot(opts.pivot,filedata)
            elif opts.group_by:
                filedata = self._groupAndAggregate(opts.group_by,filedata)
            filedata = self._sort(opts.sort,filedata)
            filedata = self._format(opts.format,filedata)


        return filedata


    def _applyFilter(self, filter: List[FilterCondition], df: pd.DataFrame) -> pd.DataFrame:
        for f in filter:
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

    def _computeColumns(self, computed_columns: Dict[str,str], df:pd.DataFrame) -> pd.DataFrame:
        if not computed_columns:
            return df

        #TODO: Dangerous... find a solution to eval
        for newcol, expr in computed_columns.items():
            df[newcol] = df.apply(lambda row: eval(expr,{},dict(row=row)), axis=1)
        return df

    def _pivot(self, pivot:Pivot, df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot_table( index=pivot.index, columns=pivot.columns, values=pivot.values, aggfunc=pivot.agg, dropna=False ).reset_index()


    def _groupAndAggregate(self, groupby:GroupBy, df: pd.DataFrame) -> pd.DataFrame:
        agg_cfg = groupby.agg
        if isinstance(agg_cfg, str):
            cols_to_agg = [c for c in df.columns if c not in groupby.columns]
            agg_cfg = {col: agg_cfg for col in cols_to_agg}

        return df.groupby(groupby.columns, dropna=True, as_index=False).agg(agg_cfg)

    def _sort(self, sort:List[SortInstruction], df: pd.DataFrame) -> pd.DataFrame:
        if sort:
            cols = [s.column for s in sort]
            asc = [s.ascending for s in sort]
            df = df.sort_values(by=cols, ascending=asc)
        return df

    def _format(self, format:Dict[str,Union[str,Dict[str,str]]], df: pd.DataFrame) -> pd.DataFrame:
        for col, fmt in format.items():
            if col in df.columns:
                if isinstance(fmt, dict):
                    df[col] = df[col].apply(lambda x: fmt.get(str(x), x))
                else:
                    try:
                        df[col] = df[col].apply(lambda x: fmt % x)
                    except Exception:
                        df[col] = df[col].astype(str)
        return df

class DataObjectParser(DataFieldParser):
    def load(self) -> dict:
        source = self.data_field.source
        if isinstance(source,DataFile):
            with open( source.filepath, "r" ) as f:
                if source.format == "json":
                    filedata = json.load(f)
                elif source.format == "csv":
                    filedata = pd.read_csv(f)
                    if not self.data_field.preprocessor:
                        self.data_field.preprocessor = Preprocessor.model_construct(module=None,function=lambda x : filedata.to_dict("list"))
                else:
                    raise NotImplementedError(f"Cannot create DataObject (Dictionnary) from {source.format} files")
        elif isinstance(source,InlineObject):
            filedata = dict(source.object)
        else:
            raise NotImplementedError(f"Cannot create a DataObject from  type {type(source)}")

        filedata = self.process(filedata)
        return filedata

class DataRawParser(DataFieldParser):
    def load(self) -> str:
        source = self.data_field.source
        if isinstance(source,DataFile):
            with open( source.filepath, "r" ) as f:
                filedata = f.read()
        elif isinstance(source,InlineRaw):
            filedata = source.value
        else:
            raise NotImplementedError(f"Cannot create a RawObject (str) from  type {type(source)}")

        filedata = self.process(filedata)
        return filedata

class DataFieldParserFactory:
    @staticmethod
    def create(data_field: DataField) -> DataFieldParser:
        type_to_parser = {
            DataTable: DataTableParser,
            DataObject: DataObjectParser,
            DataRaw:DataRawParser
        }

        parser:Type[DataFieldParser] = type_to_parser.get(type(data_field))

        if not parser:
            raise NotImplementedError(f"Unknown data field type: {data_field.type}")

        return parser(data_field)