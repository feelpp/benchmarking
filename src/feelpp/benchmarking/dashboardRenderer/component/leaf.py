from feelpp.benchmarking.dashboardRenderer.component.base import Component
from feelpp.benchmarking.dashboardRenderer.views.leaf import LeafComponentView
from feelpp.benchmarking.dashboardRenderer.repository.base import Repository

from itertools import permutations

class LeafComponent(Component):
    """"Class that represents a leaf node in a tree structure."""
    def __init__(self, item_name:str, parent_repository:Repository, parent_ids:list[str], view:LeafComponentView) -> None:
        """
        Args:
            id (str): The ID of the leaf component.
            parent_ids (list[str]): List of IDs of the parent components (unordered).
        """
        super().__init__(f"{'-'.join([p for p in parent_ids])}-{item_name}",parent_repository)
        self.view = view
        self.item_name = item_name
        self.parent_ids = parent_ids
        self.parents = []

    def addParent(self,parent:Component):
        if parent in self.parents:
            raise ValueError(f"{parent} is already a parent of {self}")
        self.parents.append(parent)

    def render(self,base_dir:str):

        perms = permutations(self.parents)
        self.view.updateTemplateData(dict(
            parent_ids = ",".join([ f"{perm[0].parent_repository.id}-{'-'.join([p.id for p in perm])}" for perm in perms ])
        ))

        self.view.render(base_dir,self.id)