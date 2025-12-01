from pydantic import field_validator,BaseModel
from typing import Optional,List
import os

class Image(BaseModel):
    url: Optional[str] = None
    filepath:str

    @field_validator("filepath", mode="after")
    @classmethod
    def checkImage(cls,v,info):
        if not info.data["url"] and not ("{{"  in v  or "}}" in v) :
            if not os.path.exists(v):
                if info.context and info.context.get("dry_run", False):
                   print(f"Dry Run: Skipping image check for {v}")
                else:
                    raise FileNotFoundError(f"Cannot find image {v}")

        return v


class Platform(BaseModel):
    image:Optional[Image] = None
    input_dir:Optional[str] = None
    options:Optional[List[str]]= []
    append_app_options:Optional[List[str]]= []
