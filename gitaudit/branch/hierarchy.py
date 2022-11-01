"""Analyse git logs to create hiearchy
"""


def take_first_parent_log(initial_sha, take_map, full_map):
    """Creates first parent log of git entries

    Args:
        initial_sha (str): start sha
        take_map (Dict[str, ChangeLogEntry]): sha map with git
            entry already considered
        full_map (Dict[str, ChangeLogEntry]): full sha map

    Returns:
        Tuple[List[ChangeLogEntry], Dict[str, ChangeLogEntry]]:
            First Parent log and take_map update
    """
    curr_entry = take_map.pop(initial_sha, None)
    fp_log = [curr_entry]

    if not curr_entry.parent_shas:
        return fp_log, take_map

    curr_first_parent_sha = curr_entry.parent_shas[0]

    while curr_first_parent_sha:
        if curr_first_parent_sha in take_map:
            curr_entry = take_map.pop(curr_first_parent_sha, None)
        else:
            curr_entry.branch_offs.append(
                full_map.get(curr_first_parent_sha, None))
            break

        fp_log.append(curr_entry)

        if not curr_entry.parent_shas:
            break

        curr_first_parent_sha = curr_entry.parent_shas[0]

    return list(reversed(fp_log)), take_map


def _recursive_hierarchy_log(initial_sha, take_map, full_map):
    hie_log, take_map = take_first_parent_log(initial_sha, take_map, full_map)

    for entry in hie_log:
        for p_sha in entry.parent_shas[1:]:
            if p_sha not in take_map:
                entry.branch_offs.append(full_map[p_sha])
            else:
                sub_log, take_map = _recursive_hierarchy_log(
                    p_sha, take_map, full_map)
                entry.other_parents.append(sub_log)

    return hie_log, take_map


def linear_log_to_hierarchy_log(lin_log):
    """Creates Hierarchy Log from linear log

    Args:
        lin_log (List[ChangeLogEntry]): Linear Log

    Returns:
        List[ChangeLogEntry]: Hierarchy Log
    """

    full_map = {x.sha: x for x in lin_log}
    take_map = {x.sha: x for x in lin_log}

    hie_log, take_map = _recursive_hierarchy_log(
        lin_log[0].sha, take_map, full_map)

    return hie_log
