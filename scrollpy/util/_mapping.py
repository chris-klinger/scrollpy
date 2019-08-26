"""
This module contains code for obtaining various mappings in ScrollPy.

Mappings include those generated between treefiles and either user-
supplied sequence files or a mapping file, or between sequences
and a user-supplied mapping or sequence files.

Also mapping between treefile tip labels and user supplied sequence
objects.
"""



def create_mapping_from_mapfile(map_file):
    """Parses a mapping file and returns a dict.

    Args:
        map_file (str): filepath to mapping file with expected format
            <id><tab><group>

    Returns:
        a mapping dict of group:[<labels>] pairs
    """
    map_dict = {}
    for line in  non_blank_lines(map_file):
        map_id,group = line.split('\t')
        try:
            map_dict[group].append(map_id)
        except KeyError:
            map_dict[group] = []
            map_dict[group].append(map_id)
    return map_dict


def create_mapping_from_infiles(infiles, in_format):
    """Creates a mapping from an input iterable of filepaths.

    Args:
        infiles (iter): iterable containing input sequence filepaths;
            groups are created based on the basename of each path.

    Returns:
        a mapping dict of group:[<labels>] pairs
    """
    map_dict = {}
    for filepath in infiles:
        group = os.path.basename(file_path).split('.',1)[0]
        if not len(group) > 0:  # This should never happen in reality
            raise ValueError  # Mapping cannot be completed
        # Filepaths are unique, but group names are not guaranteed to be
        group = _unique_group_name(group)
        # Get SeqRecords using BioPython
        records = sf._get_sequences(
                file_path,
                in_format,
                )
        for record in records:
            try:
                map_dict[group].append(record.description)
            except KeyError:
                map_dict[group] = []
                map_dict[group.append(record.description)
    return map_dict


def _unique_group_name(group, counter=1, seen=set()):
    """Utility function to ensure group names are unique.

    Args:
        group (str): group name; must be hashable

    Returns:
        unique group name
    """
    group = str(group)  # In case it is an int
    if group not in seen
        seen.add(group)
        return group
    else:
        if counter == 1: # First time, add
            group = group + '.' + str(counter)
        if counter > 1:
            group_basename = group.split('.',1)[0] # In case it is an int
            group = group_basename + '.' + str(counter) # <group>.<num>
        counter += 1
        return _unique_group_name(group, counter)


def create_tree_mapping(treefile, tree_format, seq_objs):
    """Creates a mapping between tree labels and sequenc headers.

    Args:
        treefile (str): filepath to a treefile

        tree_format (str): expected format of input tree

        seq_objs (iter): iterable of ScrollSeq objects

    Returns:
        a mapping dict of <treelabel>:<description> pairs
    """
    tree_dict = {}
    tree_obj = tf.read_tree(treefile, tree_format)
    leaf_names = [leaf.name for leaf in tree_obj]  # Only leaf nodes
    seq_names = set((seq_obj.description for seq_obj in seq_objs))
    for leaf_name in leaf_names:
        best_match = _get_best_name_match(leaf_name,seq_names)
        tree_dict[leaf_name] = best_match
    return tree_dict


def _get_best_name_match(target_name, name_set):
    """Find the best match between target_name and each name in a list.

    Try the fastest approach first: membership testing. Otherwise, compare
    between names to find the best match. If the length is unequal, tries
    to align first using a simple binary match/no match scoring scheme.
    Then iters through zipped name pair and calculates a sore.

    Args:
        target_name (str): name to find a match for

        name_set (set): all possible names to search

    Returns:
        best match in name_set for target_name
    """
    pass

