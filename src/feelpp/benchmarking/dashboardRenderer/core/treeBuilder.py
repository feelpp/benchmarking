from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema
from feelpp.benchmarking.dashboardRenderer.views.base import ViewFactory
from feelpp.benchmarking.dashboardRenderer.component.base import TreeNode,GraphNode
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.repository.leaf import LeafComponentRepository
import warnings

class ComponentTree(TreeNode):
    def __init__(self, components_config:DashboardSchema) -> None:
        super().__init__(
            "dashboard_index",
            ViewFactory.create("home",components_config.dashboard_metadata)
        )
        self.levels = components_config.component_map.component_order

        self.repositories = self.createRepositories(components_config.repositories)
        self.leaf_repository = LeafComponentRepository("leaves",components_config.component_map.mapping)

        self.buildTree(components_config)


    def createRepositories(self, repository_data):
        return [
            TreeNode( repo_id, ViewFactory.create("node",repo_data,component_id=repo_id))
            for repo_id, repo_data in repository_data.items()
        ]

    def buildTree(self,components_config: DashboardSchema):
        mapping = components_config.component_map.mapping
        components = components_config.components
        max_depth = len(self.levels)
        repo_map = {r.id : r for r in self.repositories}

        def _buildSubtree(parent_node: TreeNode, subtree: dict, depth:int = 0):
            repository_id = self.levels[depth]

            if repository_id not in components: return

            repository_components = components[repository_id]
            for node_key, node_data in subtree.items():
                if depth >= max_depth: continue

                if node_key not in repository_components: continue

                child_node = TreeNode( node_key, ViewFactory.create("node",repository_components[node_key],component_id=node_key), parent_node )
                child_node.setRepository(repo_map.get(repository_id))
                parent_node.addChild(child_node)

                if isinstance(node_data,dict) and depth + 1 < max_depth:
                    _buildSubtree(child_node,node_data, depth + 1 )

        tmp_tree = TreeNode("tmp",None)
        _buildSubtree(tmp_tree,mapping)
        leaf:GraphNode
        for leaf in self.leaf_repository:
            parent:TreeNode = tmp_tree
            for parent_id in leaf.parent_ids:
                parent = parent.get(parent_id)
            if not parent:
                warnings.warn(f"Could not find parent for leaf {leaf}")
                continue
            leaf.addParent(parent)

        view_orders = TreeUtils.treeToLists(components_config.views)
        for view_order in view_orders:
            view_perm = [self.levels.index(v) for v in view_order]
            view_tree: TreeNode = TreeUtils.permuteTree(tmp_tree,view_perm)
            parent_repository_id = view_order[0]

            repository = [repo for repo in self.repositories if repo.id == parent_repository_id]
            if not repository:
                raise ValueError(f"Repository {parent_repository_id} not defined")
            repository: TreeNode = repository[0]

            repository.setParent(self)
            for tree_child in view_tree.children:
                repository.addChild(tree_child)
                tree_child.parents.remove(view_tree)

        tmp_tree.unlink()
        del tmp_tree

        for leaf in self.leaf_repository:
            branches_to_rm = []
            for branch in leaf.getPathToRoot():
                if self not in branch:
                    branches_to_rm.append(branch)
            for b in branches_to_rm:
                for c in b[-1].children:
                    c.parents.remove(b[-1])
                b[-1].children.clear()

    def render(self,base_path):
        super().render(base_path,None,renderLeaves=False)
        self.leaf_repository.render(base_path,self.id)