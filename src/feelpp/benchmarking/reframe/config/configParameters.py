from __future__ import annotations
from pydantic import BaseModel, model_validator, field_validator
from typing import  Union, Optional, List, Any, Dict


class Linspace(BaseModel):
    min:Union[float,int]
    max:Union[float,int]
    n_steps:int

class Geomspace(Linspace):

    @field_validator("min","max",mode="after")
    @classmethod
    def checkForZero(cls,v):
        if v == 0:
            raise ValueError("Geomspace cannot contain 0")
        return v

    @model_validator(mode="after")
    def checkZeroInRange(self):
        if (self.min < 0 and self.max > 0) or (self.max < 0 and self.min>0):
            raise ValueError("0 cannot be contained between min and max")

class Range(BaseModel):
    min:Union[float,int]
    max:Union[float,int]
    step:Union[float,int]

class Geometric(BaseModel):
    start:Union[float,int]
    ratio:Union[float,int]
    n_steps:int

class Repeat(BaseModel):
    value: Any
    count: int

class Parameter(BaseModel):
    name:str
    mode:str = None
    active:Optional[bool] = True

    linspace:Optional[Linspace] = None
    geomspace:Optional[Geomspace] = None
    range:Optional[Range] = None
    sequence:Optional[List[Union[int,float,str,Dict]]] = None
    repeat:Optional[Repeat] = None
    zip:Optional[List[Parameter]] = None
    geometric: Optional[Geometric] = None

    @model_validator(mode="after")
    def setMode(self):
        if self.geomspace is not None:
            self.mode = "geomspace"
        elif self.linspace is not None:
            self.mode = "linspace"
        elif self.range is not None:
            self.mode = "range"
        elif self.geometric is not None:
            self.mode = "geometric"
        elif self.zip is not None:
            self.mode = "zip"
        elif self.sequence is not None:
            self.mode = "sequence"
        elif self.repeat is not None:
            self.mode = "repeat"
        else:
            raise NotImplementedError("Parameters need an implemented generator")

        assert len([mode for mode in [self.linspace,self.geomspace,self.geometric,self.range,self.zip,self.sequence,self.repeat] if mode is not None]) == 1, "Parameter can only have one generator"

        return self