from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import Metadata
import os

class Component:
    def __init__(self, id:str, metadata: Metadata) -> None:
        self.id = id
        self.initBaseController(metadata)

        self.views = {}

    def initBaseController(self,metadata:Metadata):

        self.index_page_controller:Controller = BaseControllerFactory.create("index")
        self.index_page_controller.updateData(dict(
            title = metadata.display_name,
            description = metadata.description,
            card_image = f"ROOT:{self.id}.jpg"
        ))

    def __repr__(self):
        return f"<{self.id}>"

    def render(self,base_dir:str, parent_id, views = None) -> None:
        views = self.views if views is None else views

        component_dir = os.path.join(base_dir,self.id)
        if not os.path.isdir(component_dir):
            os.mkdir(component_dir)

        self.index_page_controller.render(component_dir, parent_ids = parent_id, self_id = f"{parent_id}-{self.id}")

        for _, children_views in views.items():
            for children_component,children_view in children_views.items():
                children_component.render(
                    component_dir,
                    parent_id = f"{parent_id}-{self.id}",
                    views = children_view
                )
