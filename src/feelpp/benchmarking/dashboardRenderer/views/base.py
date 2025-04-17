from typing import Union
import os
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
from feelpp.benchmarking.dashboardRenderer.renderer import BaseRendererFactory
from feelpp.benchmarking.dashboardRenderer.views.templateDataHandler import TemplateDataHandlerFactory

class View:
    def __init__(
            self,
            base_template_type:str,
            template_info:TemplateInfo,
            template_data_dir:str = None,
            base_template_data:dict = {},
            out_filename:str = None
        ) -> None:
        self.renderer = self.initRenderer(base_template_type,template_info.template)
        self.out_filename = out_filename
        self.updateTemplateData(base_template_data)
        if template_info.template:
            self.addExtraTemplate(template_info.template)

        for data in template_info.data:
            self.updateTemplateData(data,template_data_dir)

    def initRenderer(self,base_template_type,template = None):
        renderer = BaseRendererFactory.create(
            base_template_type,
            os.path.dirname(template) if template else None
        )
        return renderer

    def addExtraTemplate(self,template):
        if "extra_templates" not in self.renderer.template_data:
            self.renderer.template_data["extra_templates"] = []
        self.renderer.template_data["extra_templates"].append(os.path.basename(template))

    def updateTemplateData(self,data:Union[TemplateDataFile,dict],template_data_dir:str = None):
        assert hasattr(self,"renderer") and self.renderer is not None
        handler = TemplateDataHandlerFactory.getHandler(data,template_data_dir)
        template_data = handler.extractData(data)
        self.renderer.template_data.update(template_data)

    def render(self,output_dirpath,filename = None):
        filename = filename or self.out_filename
        if not filename:
            raise ValueError(f"Filename must be set")
        if not os.path.isdir(output_dirpath):
            os.mkdir(output_dirpath)

        self.renderer.render(os.path.join(output_dirpath,filename))


class ViewFactory:
    @staticmethod
    def create(
        component_type:str,
        template_info:TemplateInfo,
        template_data_dir:str = None,
        component_id: str = None
    ):
        template_type_map = dict(
            home = dict(
                base_template_data = dict(),
                filename = "index.adoc",
            ),
            node = dict(
                base_template_data = dict(
                    self_id = component_id,
                    parent_ids = "dashboard_index",
                    card_image = f"ROOT:{component_id}.jpg"
                ),
                filename = "index.adoc"
            ),
            leaf = dict(
                base_template_data = dict( title = component_id ),
                filename = None
            )
        )
        if component_type not in template_type_map:
            raise NotImplementedError(f"Component type {component_type} not implemented")

        return View(
            component_type,
            template_info,
            template_data_dir,
            template_type_map[component_type]["base_template_data"],
            template_type_map[component_type]["filename"]
        )
