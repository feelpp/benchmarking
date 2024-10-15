from feelpp.benchmarking.report.base.baseComponent import BaseComponent
import os

class Application(BaseComponent):
    """ Class representing an application module/component.
    Inherits from BaseComponent.
    Should be used to store information related to benchmarks of an application.
    """
    def __init__(self, id, display_name, description, overview_plots):
        super().__init__(id, display_name, description)
        self.type = "application"
        self.overview_plots = overview_plots

    def createOverviews(self,base_dir, renderer):
        for use_case, keys in self.model_tree["children"].items():
            for machine, overview_model in keys["children"].items():

                renderer.render(
                    os.path.join(base_dir,self.id,use_case.id,machine.id,"overview.adoc"),
                    data = dict(
                        parent_catalogs = f"{self.id}-{use_case.id}-{machine.id}",
                        reports_df = overview_model.master_df.to_dict(),
                        use_case = use_case,
                        machine = machine,
                        application = self
                    )
                )
