"""
This module contains functions for working with ETE3 tree objects.
"""


def is_node_monophyletic(node_obj, leafseq_list):
    """Checks node monophyly based on group.

    Given a LeafSeq object, checks whether all its child nodes share
    the same group attribute.

    Args:
        node_obj     (obj) : ETE3 TreeNode object.
        leafseq_list (list): List of all associated LeafSeq objects.

    Returns:
        bool: True if node is monophyletic.

    """
    groups = get_node_groups(node_obj, leafseq_list)
    if len(groups) == 1:
        return True
    return False


def get_node_groups(node_obj, leafseq_list):
    """Gets all group names under a given node.

    Args:
        node_obj     (obj) : ETE3 TreeNode object.
        leafseq_list (list): List of all associated LeafSeq objects.

    Returns:
        set: A set of all group attributes of child LeafSeq objects.

    """
    groups = set()
    for leaf in node_obj:
        name = leaf.name
        for leafseq in leafseq_list:
             if leafseq.name == name:
                 groups.add(leafseq._group)
    return groups


def last_monophyletic_ancestor(node_to_check, leafseq_list, previous_node=None):
    """Finds the last ancestor of a node that is still monophyletic.

    Recursively moves up nodes to find the last monophyletic ancestor.

    Args:
	node_to_check (obj)           : ETE3 TreeNode object.
	leafseq_list  (list)          : List of all associated LeafSeq objects.
	previous_node (obj, optional) : ETE3 TreeNode object. Defaults to None.

    Returns:
	obj: ETE3 TreeNode object representing most ancestral monophyletic node.
            If starting node is not monophyletic, returns None instead.

    """
    if is_node_monophyletic(node_to_check, leafseq_list):
        target = node_to_check.up  # Parent node
        return last_monophyletic_ancestor(target, leafseq_list, node_to_check)
    else:  # Basecase
        return previous_node  # Last node that was monophyletic


def get_group_outgroup(tree_obj, target_leaf, group_list):
    """
    For a given group of sequences, determines whether they can be used to
    root the tree, in order to be able to look for the target_leaf.

    Essentially, checks whether the common ancestor node of the group itself
    includes the target_sequence, or, if the ancestor node is actually the
    root, whether or not either of the sister node's children are the
    sequence itself.

    Could also check for monophyly?

    Args:
	tree_obj (obj)    : ETE3 Tree/TreeNode object.
	target_leaf (str) : Name of leaf to place (same as node.name).
	group_list (list) : List of TreeNode objects for a group.

    Returns:
	obj: ETE3 TreeNode object of a node to use for rerooting. If no
            ancestral node can be used to reroot, returns False instead.

    """
    # Find common ancestor of all leaves
    if len(group_list) == 1:
        common_ancestor = group_list[0].up
    else:
        common_ancestor = tree_obj.get_common_ancestor(group_list)
    # Check whether it is root - try again
    if common_ancestor.is_root():
        return None
    else:  # Internal node
        # Node can't already contain sequence of interest
        for leaf in common_ancestor:
            if leaf.name == target_leaf:
                return None
        # Also, target sequence can't be sister group
        next_ancestor = common_ancestor.up
        for node in next_ancestor.children:
            if not node == common_ancestor:  # I.E., get sister
                if node.is_leaf():
                    if node.name == target_leaf:
                        return None
    return common_ancestor


def is_complete_group(node_object, group_list):
    """
    For a given node and a list of node objects for a given group, checks
    whether all members of the group are leaves under the given node.

    Essentially, checks whether a given node is a parent to all members of
    a group or if there are members present elsewhere in the tree.

    Args:
        node_object (obj): ETE3 Tree/TreeNode object.
        group_list (list): List of TreeNodee objects for a group.

    Returns:
        True is all nodes in group_list are leaves under node_object.

    """
    group_leaves = [leaf for leaf in node_object if leaf in group_list]
    if len(group_leaves) != len(group_list):
        return False
    return True


def get_total_support(tree_obj):
    """
    Adds up support over all nodes in a given tree object.

    Args:
        tree_obj (obj): ETE3 Tree object.

    Returns:
        int: total of all node support values.

    """
    # By default, leaf nodes have support of 1.0
    # Could restrict to stritly bifurcating?
    supports = [node.support for node in tree_obj.traverse()
            if len(node.children) > 1]
    return sum(supports)

