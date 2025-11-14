from typing import Set, Optional, Callable,List
from feelpp.benchmarking.dashboardRenderer.views.base import View
import os

class GraphNode:
    """ Base class for components """
    def __init__(self, id: str, view: View, parents: Optional[Set["GraphNode"]] = None) -> None:
        """
        Args:
            id (str): The ID of the component.
            parent_repository (Repository) : Parent Repository
        """
        self.id = id
        self.view = view
        self.repository: Optional[GraphNode] = None
        self.parents: Set[GraphNode] = parents or set()
        self.children:Set[GraphNode] = set()

        for parent in self.parents:
            parent.addChild(self)

    def unlink(self):
        for child in self.children:
            if self in child.parents:
                child.parents.remove(self)
            child.unlink()
        self.children.clear()


    def setRepository(self, repository: "GraphNode"):
        self.repository = repository

    def traverse(self, fn: Callable, level:int = 0 ):
        fn(self,level)
        for child in self.children:
            child.traverse(fn, level+1)

    def __repr__(self):
        return f"<{self.id}>"

    def print(self) -> None:
        self.traverse(lambda node, level : print("\t"*level,node))

    def addParent(self,parent: "GraphNode"):
        if parent not in self.parents:
            self.parents.add(parent)

        if self not in parent.children:
            parent.children.add(self)

    def addChild(self, child: "GraphNode") -> None:
        """Add a child node to this node"""
        existing = [c for c in self.children if c.id == child.id]
        if existing:
            for grandchild in child.children:
                existing[0].addChild(grandchild)
        else:
            self.children.add(child)
            child.parents.add(self)

    def isRoot(self):
        return len(self.parents) == 0

    def isLeaf(self):
        return len(self.children) == 0

    def getLeaves(self) -> List ["GraphNode"]:
        leaves = []
        if self.isLeaf():
            return [self]
        else:
            for child in self.children:
                leaves += child.getLeaves()

        return leaves

    def clone(self) -> "GraphNode":
        new_comp = GraphNode(self.id, self.view.clone() if self.view else None)
        new_comp.repository = self.repository
        new_comp.children = set()
        return new_comp

    def get(self,child_id:str):
        for child in self.children:
            if child.id == child_id:
                return child
        return None

    def getPathToRoot(self) -> List[List["GraphNode"]]:
        if self.isRoot():
            return [[self]]  # base case: path from root to itself

        paths = []
        for parent in self.parents:
            for parent_path in parent.getPathToRoot():
                paths.append([self] + parent_path)
        return paths

    def render(self,base_dir:str, parent_id:str = None, renderLeaves = True) -> None:
        new_parent_id = f"{parent_id}-{self.id}" if parent_id else f"{self.id}"

        if self.isRoot():
            component_dir = base_dir
        else:
            component_dir = os.path.join(base_dir,self.id)
            self.view.updateTemplateData(dict(
                parent_ids = parent_id,
                self_id_path = new_parent_id,
                self_id = self.id,
                self_repo_type = self.repository.id if self.repository else None
            ))


        self.view.render(component_dir)
        for child in self.children:
            if not renderLeaves and child.isLeaf():
                continue

            child.render(component_dir,new_parent_id,renderLeaves)


    def upstreamViewData(self, aggregator:Callable):
        child_results = [ child.upstreamViewData(aggregator) for child in self.children ]
        result = aggregator(
            self.id,
            self.repository.id if self.repository else None,
            self.view.template_data,
            child_results
        )
        self.view.template_data["aggregated"] = result
        return result


class TreeNode(GraphNode):
    def __init__(self,id:str, view: View, parent:Optional["GraphNode"] = None) -> None:
        super().__init__(id,view,{parent} if parent else set())

    def setParent(self,parent: GraphNode):
        self.parents = {parent}
        if self not in parent.children:
            parent.children.add(self)
