from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo
from feelpp.benchmarking.dashboardRenderer.views.base import View


class LeafComponentView(View):
    def __init__(self, id, template_info: TemplateInfo, base_path:str = None):
        self.id = id
        super().__init__(template_info,base_path)

    def render(self,output_dirpath, filename):
        super().render(output_dirpath,f"{filename}.adoc")

    def initRenderer(self,template = None):
        return super().initRenderer(template,"leaf")

    def initBaseTemplateData(self,renderer):
        renderer.template_data.update(
            title = self.id
        )
        return renderer