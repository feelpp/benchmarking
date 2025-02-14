from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import Metadata
import os

class Component:
    def __init__(self, id:str, metadata: Metadata, parent_id) -> None:
        self.id = id
        self.parent_id = parent_id
        self.initBaseController(metadata)

        self.views = {}

    def initBaseController(self,metadata:Metadata):

        self.index_page_controller:Controller = BaseControllerFactory.create("index")
        self.index_page_controller.updateData(dict(
            title = metadata.display_name,
            self_id = self.id,
            parent_ids = self.parent_id,
            description = metadata.description,
            card_image = ""
        ))

    def __repr__(self):
        return f"<{self.id}>"

    def render(self,base_dir:str) -> None:
        component_dir = os.path.join(base_dir,self.id)
        if not os.path.isdir(component_dir):
            os.mkdir(component_dir)
        self.index_page_controller.render(component_dir)
