from feelpp.benchmarking.dashboardRenderer.component.base import Component
from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from typing import Self
from feelpp.benchmarking.dashboardRenderer.views.base import View
import os

class NodeComponent(Component):
    """ Class representing a node component"""
    def __init__(self, id:str, parent_repository:Repository, view:View) -> None:
        """
        Args:
            id (str): The ID of the node component.
        """
        super().__init__(id,parent_repository)
        self.view = view
        self.views = {}

    def printViews(self, views:dict[str,dict[Self,dict]] = None, tab:int = 2) -> None:
        """
        Print the views of the component in a structured format.
        Args:
            views (dict, optional): The views to print. Defaults to None.
            tab (int, optional): The current indentation level. Defaults to 2.
        """
        views = self.views if views is None else views

        if not isinstance(views, dict):
            return

        for _, childrenViews in views.items():
            for component, childrenViews in childrenViews.items():
                if isinstance(childrenViews,dict):
                    print(f"{'\t' * tab}{component.id}")
                    component.printViews(childrenViews, tab + 1)
                elif isinstance(childrenViews, list):
                    print(f"{'\t' * tab}{component.id} -> {len(childrenViews)}")

    def render(self,base_dir:str, parent_id, views:dict[str,dict[Self,dict]] = None) -> None:
        views = self.views if views is None else views

        component_dir = os.path.join(base_dir,self.id)

        self.view.updateTemplateData(dict(
            parent_ids = parent_id,
            self_id = f"{parent_id}-{self.id}"
        ))
        self.view.render(component_dir)

        if not isinstance(views,dict):
            return

        for _, sub_views in views.items():
            for children_component,children_views in sub_views.items():
                children_component.render(
                    component_dir,
                    parent_id = f"{parent_id}-{self.id}",
                    views = children_views
                )

    def upstreamView( self,views:dict[str,dict[Self,dict]] = None,
                        parent_id = None,
                      dataCb = lambda parent_id, component_id ,component_data : component_data.update({parent_id:component_id}),
                      leafCb = lambda leaves_info : [leaf_data.update({parent_id:leaf_id}) for (parent_id, leaf_id, leaf_data) in leaves_info] ):

        views = self.views if views is None else views

        if not isinstance(views, dict):
            return

        child_results = []

        for _, childrenViews in views.items():
            for child_node, child_views in childrenViews.items():
                if isinstance(child_views, dict):
                    child_node.upstreamView(child_views, f"{parent_id}-{self.id}", dataCb, leafCb)
                    child_results.append(child_node.view.template_data)
                elif isinstance(child_views, list):
                    result = leafCb(f"{parent_id}-{self.id}-{child_node.id}",[(l.id,l.view.template_data) for l in  child_views])
                    child_results.append(result)

        if child_results:
            combined = dataCb(self.parent_repository.id, f"{parent_id}-{self.id}", child_results)
            self.view.updateTemplateData(combined)