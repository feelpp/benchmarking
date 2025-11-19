from typing import Dict, List, Any, Union, Optional

class Node:
    def isLeaf(self) -> bool: ...
    def clone(self) -> 'Node': ...
    def addChild(self, child: 'Node') -> None: ...
    @property
    def children(self) -> List['Node']: ...
    @property
    def id(self) -> str: ...

class TreeUtils:
    """
    A utility class containing static methods for manipulating and transforming
    hierarchical data structures, primarily Python dictionaries and custom tree nodes.
    """
    @staticmethod
    def dictTreeToLists(tree: Dict[str,Any], prefix:List[str]=[]) -> List[List[Any]]:
        """ Converts a nested dictionary structure (a 'dict tree') into a flat list of lists (paths).

        Each inner list represents a full path from the root of the input dictionary down to a leaf value. The path includes the keys and ends with the leaf value.

        Args:
            tree (Dict[str, Any]): The input dictionary tree to be traversed.
            prefix (List[Any], optional): The current path leading to the 'tree' dictionary. Used internally for recursive calls. Defaults to [].

        Returns:
            List[List[Any]]: A list where each element is a list representing a full path from root to a leaf value.

        Example:
            Input: {'A': {'B': 10, 'C': 20}, 'D': 30}
            Output: [['A', 'B', 10], ['A', 'C', 20], ['D', 30]]
        """
        tree_list = []
        for k, v in tree.items():
            new_prefix = prefix + [k]
            if isinstance(v, dict):
                tree_list.extend( TreeUtils.dictTreeToLists( v, new_prefix ) )
            else:
                tree_list.append( new_prefix + [v] )
        return tree_list


    @staticmethod
    def mergeDicts( a:Dict[Any,Any], b:Dict[Any,Any] ) -> Dict[Any,Any]:
        """
        Recursively merges dictionary `b` into dictionary `a`.

        When a key exists in both dictionaries:
        - If both values are dictionaries, the merge is applied recursively.
        - Otherwise, the value from `b` overrides the value in `a`.

        Args:
            a (Dict[Any, Any]): The target dictionary (base) which will be modified/copied.
            b (Dict[Any, Any]): The source dictionary whose contents are merged into `a`.

        Returns:
            Dict[Any, Any]: A new dictionary containing the recursive merge result.
        """
        result = a.copy()
        for key, value in b.items():
            if key in result and isinstance( result[key], dict ) and isinstance( value, dict ):
                result[key] = TreeUtils.mergeDicts( result[key], value )
            else:
                result[key] = value
        return result

    @staticmethod
    def permuteTree( root: Node, perm: List[int], permuteLeaves:bool = False ) -> Node:
        """
        Permutes the hierarchical structure of a custom tree based on an index permutation.

        This method traverses the original tree, extracts the paths to all leaves,
        and uses the `perm` indices to reconstruct a new tree where the nodes on the path are reordered according to the permutation.

        Args:
            root (Node): The root node of the original tree structure.
            perm (List[int]): A list of indices defining the new order of levels in the path (e.g., [1, 0, 2] means the new path
                              will use the second node, then the first, then the third).
            permuteLeaves (bool, optional): If True, the leaf node itself is included in the permutation. If False, the leaf node
                                            is always fixed at the end of the new path. Defaults to False.
        Returns:
            Node: The root node of the newly constructed, permuted tree.
        """
        def _collectPaths( node : Node, path:List[Node] = [] ) -> List[Node]:
            path = path + [node]
            if node.isLeaf():
                return [path]

            paths = []
            for c in node.children:
                paths.extend( _collectPaths( c, path ) )
            return paths

        leaf_paths = _collectPaths( root )
        new_root = root.clone()

        for path in leaf_paths:
            path_below_root = path[1:]  # exclude root
            if not path_below_root:
                continue

            # If we don't want to permute leaves, exclude the last node from permutation
            if not permuteLeaves:
                fixed_leaf = path_below_root[-1]
                path_to_permute = path_below_root[:-1]
            else:
                fixed_leaf = None
                path_to_permute = path_below_root

            parent_node = new_root
            current_level = {child.id: child for child in new_root.children}

            # Build permuted path
            for idx in perm:
                if idx >= len(path_to_permute):
                    continue  # skip missing levels

                orig_node:Node = path_to_permute[idx]
                node_found = current_level.get( orig_node.id )
                if node_found is None:
                    node_found = orig_node.clone()
                    parent_node.addChild( node_found )

                parent_node = node_found
                current_level = {child.id: child for child in node_found.children}

            if not permuteLeaves and fixed_leaf is not None:
                if fixed_leaf.id not in {c.id for c in parent_node.children}:
                    parent_node.addChild( fixed_leaf )

        return new_root
