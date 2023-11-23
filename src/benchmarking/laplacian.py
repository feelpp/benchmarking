import feelpp
from ._laplacian import *
import json

_laps = {
    'laplacian(2,1)': Laplacian2DP1,
    'laplacian(2,2)': Laplacian2DP2,
}


def get(dim=2, order=1, worldComm=None):
    """create a Laplacian operator

    """
    if worldComm is None:
        worldComm = feelpp.Environment.worldCommPtr()
    key = 'laplacian('+str(dim)+','+str(order)+')'
    if key not in _laps:
        raise RuntimeError('Laplacian'+key+' is not available')
    return _laps[key]()

def loadSpecs(jsonfile):
    # Reading the JSON file
    with open(jsonfile, 'r') as file:
        data = json.load(file)
    return data

