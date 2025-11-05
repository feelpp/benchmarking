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

    def upstreamView( self, parent_ids, views: dict[str, dict[Self, dict]] = None ):
        """
        Recursively build hierarchical overviews of the component tree.
        Each node's overview is a concatenated DataFrame of its children.
        """
        views = self.views if views is None else views
        if not isinstance(views, dict):
            return

        children_data = {}

        for _, children_views in views.items():
            for component, child_views in children_views.items():
                if isinstance(child_views, dict):
                    component.upstreamView(parent_ids + [self.id], child_views)
                    children_data[component.id] = component.view.template_data.copy()
                elif isinstance(child_views, list):
                    for leaf in child_views:
                        children_data[leaf.id] = leaf.view.template_data.copy()

        if "children" not in self.view.template_data:
            self.view.template_data["children"] = {}

        self.view.template_data["children"].update(children_data)