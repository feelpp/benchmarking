class TreeUtils:

    @staticmethod
    def dictTreeToLists(tree, prefix=[]):
        tree_list = []
        for k, v in tree.items():
            new_prefix = prefix + [k]
            if isinstance(v, dict):
                tree_list.extend(TreeUtils.dictTreeToLists(v, new_prefix))
            else:
                tree_list.append(new_prefix + [v])
        return tree_list


    def mergeDicts(a, b):
        """Recursively merge dictionaries a and b."""
        result = a.copy()
        for key, value in b.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = TreeUtils.mergeDicts(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def permuteTree(root, perm, permuteLeaves=False):
        def collect_paths(node, path=[]):
            path = path + [node]
            if node.isLeaf():
                return [path]

            paths = []
            for c in node.children:
                paths.extend(collect_paths(c, path))
            return paths

        leaf_paths = collect_paths(root)

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

                orig_node = path_to_permute[idx]
                node_found = current_level.get(orig_node.id)
                if node_found is None:
                    node_found = orig_node.clone()
                    parent_node.addChild(node_found)

                parent_node = node_found
                current_level = {child.id: child for child in node_found.children}

            if not permuteLeaves and fixed_leaf is not None:
                if fixed_leaf.id not in {c.id for c in parent_node.children}:
                    parent_node.addChild(fixed_leaf)

        return new_root
