import os, warnings, builtins
import importlib.util
from typing import Literal, Union, Optional, Any, List, Type, Dict
from pydantic import  BaseModel, field_validator, model_validator

class Preprocessor(BaseModel):
    #TODO: IMPORTANT: VERIFY SECURITY IMPLICATIONS OF DYNAMIC IMPORTS
    # Maybe support class later and/or static methods
    module:str
    function:str

    @model_validator(mode="before")
    @classmethod
    def parsePreprocessorString( cls, values ):
        if isinstance(values, str):
            if ":" not in values:
                raise ValueError(f"Preprocessor string '{values}' must be of the form 'module:function'")
            module, function = values.split(":",1)
            return {"module":module, "function":function}
        elif isinstance(values, dict):
            return values
        else:
            raise TypeError(f"Expected str or dict for Preprocessor, got {type(values)}")

    @field_validator("module",mode="after")
    @classmethod
    def setPreprocessorModule( cls, module, info ):
        if isinstance(module,str):
            try:
                module = __import__( module, fromlist=[info.data.get("function")] )
            except ImportError as e:
                if not os.path.isabs(module):
                    report_filepath = info.context.get("report_filepath", None)
                    if not report_filepath:
                        raise FileNotFoundError(f"Cannot resolve the report file path {report_filepath}")
                    report_filepath = os.path.abspath(report_filepath)

                    module = os.path.abspath( os.path.join( os.path.dirname(report_filepath), module ) )

                spec = importlib.util.spec_from_file_location(module,module)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                module = mod

        return module

    @field_validator("function",mode="after")
    def setPreprocessorFunction( cls, function, info ):
        if isinstance(function,str):
            try:
                if not hasattr( info.data["module"], function ):
                    raise AttributeError(f"Preprocessor function {function} not found in module {info.data.get('module')}.")
                function = getattr( info.data["module"], function )
            except AttributeError as e:
                raise AttributeError(f"Preprocessor function '{function}' could not be set: {e}")

        return function

    def apply(self, filedata: Any) -> Any:
        return self.function(filedata)

class DataFile(BaseModel):
    filepath: str
    format: Optional[Literal["json","csv","raw"]] = None

    @field_validator("filepath", mode="after")
    @classmethod
    def validateAndResolveFilepath(cls, filepath, info):
        if os.path.isabs(filepath):
            if not os.path.exists(filepath):
                warnings.warn(f"DataFile filepath '{filepath}' does not exist.")
                filepath = None
        else:
            report_filepath = info.context.get("report_filepath", None)
            if not report_filepath:
                raise FileNotFoundError("Cannot resolve the report file path ")
            report_filepath = os.path.abspath(report_filepath)
            filepath = os.path.abspath( os.path.join( os.path.dirname(report_filepath), filepath ) )
            if not os.path.exists(filepath):
                warnings.warn(f"DataFile filepath '{filepath}' does not exist relative to report file '{report_filepath}'.")
                filepath = None

        return filepath

    @model_validator(mode="after")
    def inferFormat( self ):
        extension_to_format = { "json":"json", "csv":"csv", "txt":"raw" }
        if self.format is None:
            _, ext = os.path.splitext( self.filepath )
            ext = ext.lower()
            ext = ext.lstrip(".").lower()
            format = extension_to_format.get(ext)
            if not format:
                warnings.warn(f"Unsupported extension {ext} for file {self.filepath}. Treating it as raw text data")
                format = "raw"
            self.format = format
        return self

class InlineTableColumn(BaseModel):
    name: str
    values: List[Any]
    dtype:Optional[Type] = None

    @field_validator("dtype", mode="before")
    def castDtype(cls, v):
        if isinstance(v, type):
            return v

        if isinstance(v, str):
            t = getattr(builtins, v, None)
            if isinstance(t, type):
                return t
            raise ValueError(f"Unsupported built-in type name '{v}'")

        raise ValueError(f"dtype must be a type or a string")


    @model_validator(mode="after")
    def castValues(self):
        if self.dtype:
            self.values = [ self.dtype(v) for v in self.values ]
        return self


class InlineTable(BaseModel):
    columns: Optional[List[InlineTableColumn]] = []

    @field_validator("columns",mode="after")
    @classmethod
    def checkColumnSize(cls,columns:List[InlineTableColumn]):
        table_len = len(columns[0].values)
        for col in columns:
            if len(col.values) != table_len:
                raise ValueError("Inline table columns should have the same length.")

        return columns

class InlineObject(BaseModel):
    object: Dict

class InlineRaw(BaseModel):
    value: str

class DataField(BaseModel):
    type: Optional[Literal["DataTable","Object","Raw"]] = None
    name: str
    preprocessor: Optional[Preprocessor] = None
    source: Union[DataFile, InlineTable, InlineObject, InlineRaw]

    expose:Optional[Union[str,bool]] = True

    @model_validator(mode="before")
    @classmethod
    def inferSource(cls,values:Dict, info):
        if "source" in values:
            return values

        if "filepath" in values:
            filepath = values.pop("filepath")
            format = values.pop("format",None)
            values["source"] = DataFile.model_validate({"filepath":filepath,"format":format}, context=info.context)
        else:
            data_type = values.get("type")
            if data_type == "DataTable":
                values["source"] = InlineTable(columns=values.get("columns"))
            elif data_type == "Object":
                values["source"] = InlineObject(object=values.get("object"))
            elif data_type == "Raw":
                values["source"] = InlineRaw(value=values.get("value"))
            else:
                raise ValueError("Data Type should be provided when passing inline data.")

        return values


    @model_validator(mode="after")
    def coerceExpose(self):
        if self.expose and isinstance(self.expose,bool):
            self.expose = self.name
        return self

    @field_validator("preprocessor",mode="before")
    @classmethod
    def passContext(cls, v:Preprocessor, info):
        if v:
            return Preprocessor.model_validate(v,context=info.context)
        return v


    @model_validator(mode="after")
    def inferTypeFromFormat(self):
        if not isinstance(self.source, DataFile):
            return self

        format_to_default_type = { "json":"Object", "csv":"DataTable", "raw":"Raw" }
        if self.type is None:
            self.type = format_to_default_type.get(self.source.format,"Raw")
        return self

class GroupBy(BaseModel):
    columns: List[str]
    agg: Union[Dict[str, str],str]


class Pivot(BaseModel):
    index: List[str]
    columns: List[str]
    values: str
    agg: str

class SortInstruction(BaseModel):
    column: str
    ascending: bool = True

class FilterCondition(BaseModel):
    column: str
    op: Literal["==", "!=", ">", "<", ">=", "<=", "in", "not in"]
    value: object


class TableOptions(BaseModel):
    computed_columns: Optional[Dict[str,str]] = {}
    format: Optional[Dict[str, Union[str,Dict[str,str]]]] = {}

    group_by: Optional[GroupBy] = None
    pivot: Optional[Pivot] = None

    sort: Optional[List[SortInstruction]] = []
    filter: Optional[List[FilterCondition]] = []


    @model_validator(mode="after")
    def validateExclusivity(self):
        if self.group_by and self.pivot:
            raise ValueError(
                "Cannot use both 'group_by' and 'pivot' in a table. "
                "Pivot already performs aggregation, so 'group_by' is redundant."
            )

        if self.group_by:
            if not self.group_by.agg or len(self.group_by.agg) == 0:
                raise ValueError("'group_by' requires an 'agg' mapping.")

        if self.pivot and self.sort:
            raise ValueError(
                "Sorting a pivoted table is ambiguous. Remove 'sort' or perform sorting before pivot."
            )

        return self


class DataTable(DataField):
    type: Optional[Literal['DataTable']] = "DataTable"
    table_options:Optional[TableOptions] = TableOptions()

class DataObject(DataField):
    type: Optional[Literal["Object"]] = "Object"

class DataRaw(DataField):
    type: Optional[Literal["Raw"]] = "Raw"