"""Tests for parameter models validation by pydantic schemas"""

import pytest
from feelpp.benchmarking.reframe.config.configParameters import Parameter, Linspace,Geomspace,Range,Geometric,Repeat
from pydantic import ValidationError


@pytest.mark.parametrize( ("mode", "parameter_type","test_values"), [
    ("linspace",Linspace,{"min":0,"max":1,"n_steps":2}),
    ("geomspace",Geomspace,{"min":1,"max":2,"n_steps":2}),
    ("range",Range,{"min":0,"max":2,"step":1}),
    ("geometric",Geometric,{"start":1,"ratio":2,"n_steps":2}),
    ("repeat",Repeat,{"value":1,"count":2}),
    ("sequence",None,["a","b","c"]),
    ("zip",None,[{"name":"param_1","linspace":{"min":0,"max":1,"n_steps":2}},{"name":"param_2","repeat":{"value":1,"count":2}}])
])
def test_parameterModes(mode,parameter_type,test_values):
    """ Tests the General Parameter logic.
        Checks that the mode is correctly assigned depending on the type
    Args:
        mode (str): Parameter mode
        parameter_type (cls): Pydantic model for the mode
        test_values (dict|list): Dummy values used to instantiate the parameter
    """
    param = Parameter(
        name="test_parameter",
        **({mode:parameter_type(**test_values)} if parameter_type else {mode:test_values})
    )
    assert param.mode == mode


def test_invalidMode():
    """Tests that correct errors are raised when assigning invalid modes"""
    with pytest.raises(NotImplementedError, match="Parameters need an implemented generator"):
        Parameter(name="test_param")
    with pytest.raises(NotImplementedError, match="Parameters need an implemented generator"):
        Parameter(name="test_param",mode="unkown_mode")
    with pytest.raises(NotImplementedError, match="Parameters need an implemented generator"):
        Parameter(name="test_param",mode="unkown")
    with pytest.raises(ValidationError, match="Parameter can only have one generator"):
        Parameter(**{"name":"multi mode param","linspace":{"min":0,"max":1,"n_steps":2},"repeat":{"value":1,"count":2} })

def validateGenerator(generator,params,raises,raises_match):
    """ Helper function to test that errors are raised (or not) depending on the model values
    Args:
        generator (cls): Pydantic parameter model
        params (dict|list): Parameter values to use for instantiation (depending on the values, they should raise errors or not)
        raises (bool) : Whether if a ValidationError is expected or not.
        raises_match (str|None): Regex pattern to look for in the case of an exception raised.
    """
    if raises:
        with pytest.raises(ValidationError, match=raises_match):
            generator(**params)
    else:
        instance = generator(**params)
        for key, value in params.items():
            assert getattr(instance, key) == value


@pytest.mark.parametrize(("min","max","n_steps","raises","raises_match"),[
    (0.5,8,3,False,None), (-1,8,3,False,None),
    (1,2,0,True,"Number of steps should be strictly positive"), (0,1,-1,True,"Number of steps should be strictly positive"),
    ("invalid",1,-1,True,"Input should be a valid number"), (0,{"a":2},-1,True,"Input should be a valid number"),
    (0,1,"c",True,"Input should be a valid integer"), (0,1,0.6,True,"Input should be a valid integer")
])
def test_linspace(min,max,n_steps,raises,raises_match):
    """Tests the Linspace generator"""
    validateGenerator(Linspace,{"min":min,"max":max,"n_steps":n_steps},raises,raises_match)


@pytest.mark.parametrize(("min","max","n_steps","raises","raises_match"),[
    (0.5,8,3,False,None), (-5,-1,3,False,None), (-5,-5,3,False,None),
    (-1,1,5,True,"0 cannot be contained between min and max"), (0,1,5,True,"Geomspace cannot contain 0"),
    (1,2,0,True,"Number of steps should be strictly positive"), (0,1,-1,True,"Number of steps should be strictly positive"),
    ("invalid",1,-1,True,"Input should be a valid number"), (0,{"a":2},-1,True,"Input should be a valid number"),
    (0,1,"c",True,"Input should be a valid integer"), (0,1,0.6,True,"Input should be a valid integer")
])
def test_geomspace(min,max,n_steps,raises,raises_match):
    """Tests the Geomspace generator"""
    validateGenerator(Geomspace,{"min":min,"max":max,"n_steps":n_steps},raises,raises_match)


@pytest.mark.parametrize(("min","max","step","raises","raises_match"),[
    (0,1,10,False,None), (1.5,10.5,1,False,None),
    (1,2,0,True,"Step cannot be 0"),
    (1,2,-1,True,"Range will result empty"),(2,1,1,True,"Range will result empty"),(1,1,3,True,"Range will result empty"),
    (1,2,"a",True,"Input should be a valid number"), ("a",2,1,True,"Input should be a valid number"),
])
def test_range(min,max,step,raises,raises_match):
    """Tests the Range generator"""
    validateGenerator(Range,{"min":min,"max":max,"step":step},raises,raises_match)


@pytest.mark.parametrize(("start","ratio","n_steps","raises","raises_match"),[
    (0.5,8,3,False,None), (-1,8,3,False,None),
    (1,2,0,True,"Number of steps should be strictly positive"), (0,1,-1,True,"Number of steps should be strictly positive"),
    ("invalid",1,-1,True,"Input should be a valid number"), (0,{"a":2},-1,True,"Input should be a valid number"),
    (0,1,"c",True,"Input should be a valid integer"), (0,1,0.6,True,"Input should be a valid integer")
])
def test_geometric(start,ratio,n_steps,raises,raises_match):
    """Tests the Geometric generator"""
    validateGenerator(Geometric,{"start":start,"ratio":ratio,"n_steps":n_steps},raises,raises_match)


@pytest.mark.parametrize(("value","count","raises","raises_match"),[
    ("a",10,False,None), (1,10,False,None), (0.5,10,False,None), (["a",1,{"c":1},{5}],10,False,None),
    (1,"x",True,"Input should be a valid integer"), (1,0.5,True,"Input should be a valid integer"),
])
def test_repeat(value,count,raises,raises_match):
    """Tests the Repeat generator"""
    validateGenerator(Repeat,{"value":value,"count":count},raises,raises_match)
