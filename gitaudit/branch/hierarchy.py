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

    return fp_log, take_map


def _recursive_hierarchy_log(initial_sha, take_map, full_map):
    hie_log, take_map = take_first_parent_log(initial_sha, take_map, full_map)

    for entry in reversed(hie_log):
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


def hierarchy_log_to_linear_log_entry(entry):
    """For a log entry remove hierarchy and return
    as linear log

    Args:
        entry (ChangeLogEntry): the log entry

    Returns:
        List[ChangeLogEntry]: Linear Log
    """

    parent_hier_logs = entry.other_parents
    lin_log = [entry.copy_without_hierarchy()]

    for p_hier_log in parent_hier_logs:
        lin_log.extend(hierarchy_log_to_linear_log(p_hier_log))

    return lin_log


def hierarchy_log_to_linear_log(hier_log):
    """For a list of log entries remove hierarchy and
    return as linear log

    Args:
        hier_log (List[ChangeLogEntry]): the list of log entries

    Returns:
        List[ChangeLogEntry]: Linear Log
    """
    lin_log = []

    for entry in hier_log:
        lin_log.extend(hierarchy_log_to_linear_log_entry(entry))

    return lin_log


def changelog_hydration(log, git, changelog_map=None):
    """Hydrates a parent log with changelog entries

    Args:
        log (List[ChangeLogEntry]): Parent log
        git (Git): Git instance
        changelog_map (Dict[str, ChangeLogEntry], optional): Dictionary sha -> ChangeLogEntry.
            Defaults to None.

    Returns:
        List[ChangeLogEntry]: Change Log
    """
    if changelog_map is None:
        end_sha = log[0].sha
        start_sha_parent_sha = \
            log[-1].parent_shas[0] if log[-1].parent_shas else None
        changelog = git.log_changelog(
            end_ref=end_sha,
            start_ref=start_sha_parent_sha,
            patch=True,
        )
        changelog_map = {x.sha: x for x in changelog}

    for index, entry in enumerate(log):
        if entry.sha in changelog_map:
            changelog_entry = changelog_map[entry.sha]
        else:
            changelog_entry = git.show_changelog_entry(entry.sha)

        assert entry.sha == changelog_entry.sha
        assert entry.parent_shas == changelog_entry.parent_shas

        log[index] = changelog_entry

        for o_parent in entry.other_parents:
            changelog_entry.other_parents.append(changelog_hydration(
                o_parent,
                git,
                changelog_map,
            ))
    return log
