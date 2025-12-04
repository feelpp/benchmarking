from typing import Union, Type, List, Dict
from feelpp.benchmarking.json_report.schemas.dataRefs import DataFile, InlineTable, InlineRaw, InlineObject,DataTable,DataObject,DataRaw,DataField, Preprocessor, ReferenceSource
from feelpp.benchmarking.json_report.schemas.dataRefs import Pivot, GroupBy, SortInstruction, FilterCondition
import pandas as pd
import json


class DataLoader:
    def __init__(self, source):
        self.source = source

    def load(self)-> Union[pd.DataFrame,dict,str]:
        raise NotImplementedError("Pure virtual function, must be implemented in child class")

class DataFileLoader(DataLoader):
    def load(self):
        if not isinstance(self.source, DataFile):
            raise ValueError(f" DataFileLoader is not supported for source type : {type(self.source)}")
        with open( self.source.filepath, "r" ) as f:
            if self.source.format == "csv":
                return pd.read_csv(f)
            elif self.source.format == "json":
                return json.load(f)
            elif self.source.format == "raw" :
                return f.read()
            else:
                raise NotImplementedError(f"Unkonwn format {self.source.format} for {self.source.filepath}")

class InlineLoader(DataLoader):
    def load(self):
        if isinstance( self.source, InlineTable):
            return pd.DataFrame({c.name:c.values for c in self.source.columns})
        elif isinstance( self.source, InlineObject):
            return dict(self.source.object)
        elif isinstance( self.source, InlineRaw):
            return str(self.source.value)
        else:
           raise NotImplementedError(f"Unkonwn inline type {type(self.source)}")

class ReferenceLoader(DataLoader):
    def __init__(self, data_graph):
        super().__init__()
        self.data_graph = data_graph

    def load(self):
        pass


class DataFieldProcessor:
    def __init__(self,data_field: Union[DataTable,DataObject,DataRaw]):
        self.data_field = data_field

    def process(self, filedata: Union[pd.DataFrame,dict,str]):
        if self.data_field.preprocessor:
            filedata = self.data_field.preprocessor.apply(filedata)
        return filedata


class DataObjectProcessor(DataFieldProcessor):
    def process(self, filedata):
        filedata = super().process(filedata)

        if isinstance(filedata,pd.DataFrame):
            filedata = filedata.to_dict(orient="list")
        elif isinstance(filedata, str):
            filedata = json.loads(filedata)

        return filedata

class DataRawProcessor(DataFieldProcessor):
    def process(self, filedata):
        filedata = super().process(filedata)

        if isinstance(filedata,pd.DataFrame):
            filedata = filedata.to_string()
        elif isinstance(filedata, dict):
            filedata = json.dumps(filedata)

        return filedata


class DataTableProcessor(DataFieldProcessor):
    def process(self, filedata):
        filedata = super().process(filedata)
        if isinstance(filedata, list):
            filedata = pd.DataFrame.from_dict(filedata,orient="columns")
        elif isinstance(filedata,dict):
            filedata = pd.DataFrame.from_dict(filedata,orient="index")
        elif isinstance(filedata,str):
            raise NotImplementedError(f"Cannot create a Table from a string: {filedata}")


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


class DataLoaderFactory:
    @staticmethod
    def create(source):
        if isinstance(source, DataFile):
            return DataFileLoader(source)
        else:
            return InlineLoader(source)
        #TODO: REF

class DataProcessorFactory:
    type_to_processor:Dict[str,Type] = {
        DataTable: DataTableProcessor,
        DataObject: DataObjectProcessor,
        DataRaw: DataRawProcessor
    }

    @classmethod
    def create(cls,data_field: DataField):
        processor:Type[DataFieldProcessor] = cls.type_to_processor.get(type(data_field))

        if not processor:
            raise NotImplementedError(f"Unknown data field type: {data_field.type}")

        return processor(data_field)


class DataFieldParser:
    def __init__(self, data_field :DataField):
        self.data_field = data_field


    def parse(self):
        loader = DataLoaderFactory.create(self.data_field.source)
        processor = DataProcessorFactory.create(self.data_field)

        filedata = loader.load()
        filedata = processor.process(filedata)

        return filedata


class DataReferenceDependencyGraph:
    def __init__(self, data_fields:List[DataField]):
        self.data_fields:Dict[str,DataField] = { f.name : f for f in data_fields}
        self.cache = {}

    def resolve(self, ref_name:str):
        if ref_name in self.cache:
            return self.cache[ref_name]

        data_field = self.data_fields.get(ref_name,None)
        if not data_field:
            raise ReferenceError(f"Cannot find data reference {ref_name} on the loaded data")

        if isinstance(data_field,ReferenceSource):
            parent = self.data_fields[data_field.source.ref]
            if not data_field.type:
                data_field.type = parent.type

        parser = DataFieldParserFactory.create(data_field=data_field, graph=self)
        result = parser.load()
        self.cache[ref_name] = result
        return result

