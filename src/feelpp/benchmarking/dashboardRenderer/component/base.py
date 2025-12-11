from typing import Set, Optional, Callable,List
from feelpp.benchmarking.dashboardRenderer.views.base import View
import os

class GraphNode:
    """
    Base class representing a node in a graph structure, typically used for
    UI components or similar hierarchical/relational entities.
    Nodes can have possible parents and children.
    """
    def __init__( self, id: str, view: View, parents: Optional[Set["GraphNode"]] = None ) -> None:
        """
        Args:
            id (str): The unique identifier of the component/node.
            view (View): The View object associated with this node, responsible for rendering.
            parents (Optional[Set[GraphNode]]): A set of parent GraphNodes. Defaults to None, meaning it is a root node.
        """
        self.id : str = id
        self.view : View = view
        self.repository : Optional[GraphNode] = None
        self.parents : Set[GraphNode] = parents or set()
        self.children : Set[GraphNode] = set()

        for parent in self.parents:
            parent.addChild( self )

    def unlink( self ) -> None:
        """
        Unlinks the node and recursively unlinks all of its children.
        This removes references to this node from its children's parent sets and clears this node's child set.
        """
        for child in self.children:
            if self in child.parents:
                child.parents.remove( self )
            child.unlink()
        self.children.clear()


    def setRepository( self, repository: "GraphNode" ) -> None:
        """
        A Repository describes a 'category' of a node. It can have a single repository.
        Args:
            repository (GraphNode): The node to be set as the repository.
        """
        self.repository = repository

    def traverse( self, fn: Callable[["GraphNode",int],None], level:int = 0 ) -> None:
        """
        Performs a depth-first traversal starting from this node.

        The provided function fn is called for this node and then recursively for all children.

        Args:
            fn (Callable[[GraphNode, int], None]): The function to execute on each node.
                                                   It takes the current node and the traversal level.
            level (int): The current depth/level in the traversal. Defaults to 0.
        """
        fn( self,level )
        for child in self.children:
            child.traverse( fn, level+1 )

    def __repr__( self ) -> str:
        return f"<{ self.id }>"

    def print( self ) -> None:
        """ Prints the node and its descendants in a tree-like structure, indicating the hierarchy level with indentation. """
        self.traverse( lambda node, level : print( "\t"*level, node ) )

    def addParent( self, parent: "GraphNode" ) -> None:
        """
        Adds a parent node and updates the parent's children set.

        Args:
            parent (GraphNode): The node to be added as a parent.
        """
        if parent not in self.parents:
            self.parents.add( parent )

        if self not in parent.children:
            parent.children.add( self )

    def addChild( self, child: "GraphNode" ) -> None:
        """
        Adds a child node to this node.

        If a child with the same ID already exists, the new child's descendants
        are moved to the existing child, and the new child is discarded.
        Otherwise, the new child is added.

        Args:
            child (GraphNode): The node to be added as a child.
        """
        existing = [c for c in self.children if c.id == child.id]
        if existing:
            for grandchild in child.children:
                existing[0].addChild( grandchild )
        else:
            self.children.add( child )
            child.parents.add( self )

    def isRoot( self ) -> bool:
        """
        Checks if the node is a root node (i.e., has no parents).

        Returns:
            bool: True if the node is a root, False otherwise.
        """
        return len( self.parents ) == 0

    def isLeaf( self ) -> bool:
        """
        Checks if the node is a leaf node (i.e., has no children).

        Returns:
            bool: True if the node is a leaf, False otherwise.
        """
        return len( self.children ) == 0

    def getLeaves( self ) -> List ["GraphNode"]:
        """
        Recursively gets all leaf nodes descending from this node (including this node if it is a leaf).

        Returns:
            List[GraphNode]: A list of all leaf nodes in the subtree.
        """
        leaves = []
        if self.isLeaf():
            return [ self ]
        else:
            for child in self.children:
                leaves += child.getLeaves()

        return leaves

    def clone( self ) -> "GraphNode":
        """
        Creates a shallow clone of the GraphNode.

        The clone has the same ID, a cloned view (if it exists), and the same repository.
        It does *not* clone parents or children; the children set is empty.

        Returns:
            GraphNode: The new, cloned GraphNode instance.
        """
        new_comp = GraphNode( self.id, self.view.clone() if self.view else None )
        new_comp.repository = self.repository
        new_comp.children = set()
        return new_comp

    def get( self, child_id:str ) -> Optional["GraphNode"]:
        """
        Retrieves a direct child node by its ID.

        Args:
            child_id (str): The ID of the child node to retrieve.

        Returns:
            Optional[GraphNode]: The child node if found, otherwise None.
        """
        for child in self.children:
            if child.id == child_id:
                return child

    def getPathToRoot( self ) -> List[List["GraphNode"]]:
        """
        Finds all possible paths from this node up to any root node.

        Each path is a list of GraphNodes starting from the current node and ending at a root.

        Returns:
            List[List[GraphNode]]: A list of paths (where each path is a list of GraphNodes).
        """
        if self.isRoot():
            return [[self]]  # base case: path from root to itself

        paths = []
        for parent in self.parents:
            for parent_path in parent.getPathToRoot():
                paths.append([self] + parent_path)
        return paths

    def render( self, base_dir:str, parent_id:str = None, renderLeaves = True ) -> None:
        """
        Renders the node's view and recursively calls render on its children.

        Rendering involves updating the view's template data with hierarchical information
        and calling the view's render method to create output (e.g., files or components).

        Args:
            base_dir (str): The base directory for rendering output.
            parent_id (Optional[str]): The path ID of the parent node (if any). Defaults to None.
            renderLeaves (bool): If False, rendering stops at the leaf nodes. Defaults to True.
        """
        new_parent_id = f"{parent_id}-{self.id}" if parent_id else f"{self.id}"

        if self.isRoot():
            component_dir = base_dir
        else:
            component_dir = os.path.join(base_dir,self.id)
            self.view.updateTemplateData( dict(
                parent_ids = parent_id,
                self_id_path = new_parent_id,
                self_id = self.id,
                self_repo_type = self.repository.id if self.repository else None
            ) )


        self.view.renderExtra( component_dir )
        self.view.render( component_dir )
        for child in self.children:
            if not renderLeaves and child.isLeaf():
                continue

            child.render( component_dir, new_parent_id, renderLeaves )


    def upstreamViewData( self, aggregator: Callable[[str, Optional[str], dict, List], dict] ) -> dict:
        """
        Aggregates data from child nodes' views up to this node.

        Recursively collects data from children, passes it to the `aggregator` function
        along with this node's data, updates this node's view template data with the
        aggregated result, and returns the result.

        Args:
            aggregator (Callable[[str, Optional[str], dict, List], dict]): A function that
                takes (node_id, repository_id, template_data, child_results) and returns
                the aggregated data for this node.

        Returns:
            dict: The aggregated data for this node.
        """
        child_results = [ child.upstreamViewData( aggregator ) for child in self.children ]
        result = aggregator(
            self.id,
            self.repository.id if self.repository else None,
            self.view.template_data,
            child_results
        )
        self.view.template_data["aggregated"] = result
        return result


class TreeNode(GraphNode):
    """
    A specialized GraphNode that enforces a strict tree structure (single parent).
    """
    def __init__( self, id:str, view: View, parent:Optional["GraphNode"] = None ) -> None:
        """
        Args:
            id (str): The unique identifier of the component/node.
            view (View): The View object associated with this node.
            parent (Optional[GraphNode]): The single parent GraphNode. Defaults to None.
        """
        super().__init__( id, view, {parent} if parent else set() )

    def setParent( self, parent: GraphNode ) -> None:
        """
        Sets the single parent for this TreeNode and updates the parent's children set.

        Args:
            parent (GraphNode): The node to be set as the parent.
        """
        self.parents = {parent}
        if self not in parent.children:
            parent.children.add( self )
