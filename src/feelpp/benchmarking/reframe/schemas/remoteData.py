from pydantic import BaseModel, model_validator
from typing import Optional

class BaseRemoteData(BaseModel):
    destination: str

class RemoteGirderData(BaseModel):
    item: Optional[str] = None
    file: Optional[str] = None
    folder: Optional[str] = None

    @model_validator(mode="after")
    def checkValidResource(self):
        if all(res is None for res in [self.item, self.file, self.folder]):
            raise ValueError("A valid resource needs to be specified, either 'file', 'folder' or 'item'")
        return self

class RemoteData(BaseRemoteData):
    girder: Optional[RemoteGirderData] = None

    @model_validator(mode="after")
    def checkRemoteDataPlatform(self):
        if all(plat is None for plat in [self.girder]):
            raise ValueError("A remote data platform should be specified, valid options are ['girder'] ")
        return self
