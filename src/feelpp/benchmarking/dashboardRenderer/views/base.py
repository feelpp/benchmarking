from typing import Union
from datetime import datetime
import os, shutil
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
from feelpp.benchmarking.dashboardRenderer.renderer import BaseRendererFactory
from feelpp.benchmarking.dashboardRenderer.views.templateDataHandler import TemplateDataHandlerFactory

class View:

    plugins = {}

    def __init__(
            self,
            base_template_type:str,
            template_info:TemplateInfo,
            template_data_dir:str = None,
            base_template_data:dict = {},
            out_filename:str = None
        ) -> None:
        self.partials = {}
        self.renderer = self.initRenderer(base_template_type,template_info.template)


        self.template_data = {}
        self.updateTemplateData(base_template_data)

        self.out_filename = out_filename
        self.template_info = template_info
        self.template_data_dir = template_data_dir


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
        if "extra_templates" not in self.template_data:
            self.template_data["extra_templates"] = []
        self.template_data["extra_templates"].append(os.path.basename(template))

    def updateTemplateData(self,data:Union[TemplateDataFile,dict],template_data_dir:str = None):
        assert hasattr(self,"renderer") and self.renderer is not None
        handler = TemplateDataHandlerFactory.getHandler(type(data),template_data_dir)
        template_data = handler.extractData(data,self.partials)
        self.template_data.update(template_data)
        self.processPlugins()

    def copyPartials(self,base_dir:str,pages_dir:str) -> None:

        for prefix, path in self.partials.items():
            local_partial_path = os.path.join(base_dir,prefix)
            shutil.copytree(path, local_partial_path)
            self.updateTemplateData({prefix:os.path.relpath(local_partial_path,pages_dir)})

    def render(self,output_dirpath,filename = None):
        filename = filename or self.out_filename
        if not filename:
            raise ValueError(f"Filename must be set")
        if not os.path.isdir(output_dirpath):
            os.mkdir(output_dirpath)

        self.renderer.render(os.path.join(output_dirpath,filename),self.template_data)

    def processPlugins(self):
        for pluginName, plugin in self.plugins.items():
            self.template_data.update({pluginName:plugin.process(self.template_data)})

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
                base_template_data = dict(
                    title = "My Dashboard",
                    datetime = datetime.strftime(datetime.now(),format="%Y-%m-%d:%H:%M:%S")
                ),
                filename = "index.adoc",
            ),
            node = dict(
                base_template_data = dict(
                    title = "Default Repository",
                    description = "Default Description",
                    self_id = component_id or "default_repository",
                    parent_ids = "dashboard_index",
                    card_image = f"ROOT:{component_id}.jpg" if component_id else "ROOT:default-image.jpg",
                ),
                filename = "index.adoc"
            ),
            leaf = dict(
                base_template_data = dict(
                    title = component_id or "Default Leaf",
                    self_id = "default_leaf",
                    parent_ids = "dashboard_index",
                    description = "Default Leaf Description",
                    card_image = "ROOT:default-image.jpg"
                ),
                filename = "leaf.adoc",
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


class PreRenderPlugin:
    """Interface for a plugin
    Uses the view template data to parse it and store it using the plugin name"""
    def process(self, template_data: dict) -> dict:
        raise NotImplementedError