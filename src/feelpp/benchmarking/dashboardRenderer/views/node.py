from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo
from feelpp.benchmarking.dashboardRenderer.views.base import View

class NodeComponentRepositoryView(View):
    def __init__(self, component_id, template_info: TemplateInfo):
        self.component_id = component_id
        super().__init__(template_info)

    def render(self,output_dirpath):
        super().render(output_dirpath,"index.adoc")

    def initRenderer(self,template = None):
        return super().initRenderer(template,"node")

    def initBaseTemplateData(self,renderer):
        renderer.template_data.update(
            self_id = self.component_id,
            parent_ids = "dashboard_index",
            card_image = f"ROOT:{self.component_id}.jpg"
        )
        return renderer

class NodeComponentView(View):
    def __init__(self, component_id, template_info: TemplateInfo):
        self.component_id = component_id
        super().__init__(template_info)

    def render(self,output_dirpath):
        super().render(output_dirpath,"index.adoc")

    def initRenderer(self,template = None):
        return super().initRenderer(template,"node")

    def initBaseTemplateData(self,renderer):
        renderer.template_data.update(
            card_image = f"ROOT:{self.component_id}.jpg"
        )
        return renderer
