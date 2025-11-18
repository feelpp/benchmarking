from feelpp.benchmarking.dashboardRenderer.component.base import GraphNode
from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.views.base import View
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateDataFile
import os,warnings,json

class LeafComponent(GraphNode):
    """"Class that represents a leaf node in a tree structure."""
    def __init__(self, item_name:str, parent_repository:Repository, parent_ids:list[str], view:View) -> None:
        """
        Args:
            id (str): The ID of the leaf component.
            parent_ids (list[str]): List of IDs of the parent components (unordered).
        """
        super().__init__(f"{'-'.join([p for p in parent_ids])}-{item_name}",view)
        self.setRepository(parent_repository)

        self.item_name = item_name
        self.parent_ids = parent_ids

    def clone(self):
        raise RuntimeError("Leaf component cannot be cloned")

    def getPermParentIdsStr(self,parent_id:str=None):
        branches = []
        for branch in self.getPathToRoot():
            branches.append("-".join([b.id for b in branch[1:][::-1]]))
        return ",".join(branches)

    def render(self,base_dir:str,parent_id:str = None):

        self.view.updateTemplateData(dict(
            parent_ids = self.getPermParentIdsStr(parent_id)
        ))
        leaf_dir = os.path.join(base_dir,self.id)

        self.view.updateTemplateData(dict(
            self_relpath = os.path.relpath(leaf_dir,os.path.join(base_dir,"..")),
        ))

        self.view.copyPartials(leaf_dir,os.path.join(base_dir,".."))

        self.view.render(leaf_dir)

    def patchTemplateInfo(self,patch, prefix,save):
        if save:
            template_data_files = [d for d in self.view.template_info.data if isinstance(d,TemplateDataFile) and d.prefix and d.prefix == prefix ]

            if len(template_data_files) > 1:
                warnings.warn(f"More than one file having prefix {prefix} found. First occurence will be overwritten")

            filepath = None
            if len(template_data_files) == 0:
                warnings.warn(f"No data files with {prefix} found in {self.id}. Saving this patch will not be possible.")
            else:
                filepath = template_data_files[0].filepath
                format = template_data_files[0].format

            if filepath:
                with open(os.path.join(self.view.template_data_dir, filepath), "w") as f:
                    if format == "json":
                        json.dump(patch,f)
                    else:
                        f.write(patch)
        self.view.updateTemplateData({prefix:patch})