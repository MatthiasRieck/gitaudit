"""Extract sparse hierarchy from a git log
"""


from gitaudit.branch.hierarchy import take_first_parent_log, linear_log_to_hierarchy_log


def extract_sparse_lin_log(lin_log, start_sha):
    """Extracts a sparse Lineare Log
       Given a linear log and a merge commit sha
       this function will return the first parent
       log and all branching elements
       from the start sha up until the point
       where are merge branches are branched off

    Args:
        lin_log (List[ChangeLogEntry]): Linear Log of change log lin_log
        start_sha (str): Sha to start the search from

    Returns:
        List[ChangeLogEntry]: Linear log containing only the relevant
            lin_log
    """
    full_map = {x.sha: x for x in lin_log}
    take_map = {x.sha: x for x in lin_log}

    # create first parent log and first parent shas
    fpl, take_map = take_first_parent_log(lin_log[0].sha, take_map, full_map)
    fpl_shas = list(map(lambda x: x.sha, fpl))

    # collect all relevant lin_log until the first parent linear log is reached
    start_entry = full_map[start_sha]
    analysis_stack = {start_entry.sha: start_entry}
    analysis_lin_log = {}

    fpl_branch_off_shas = []

    while analysis_stack:
        entry = analysis_stack.pop(list(analysis_stack)[0])
        analysis_lin_log[entry.sha] = entry

        for sha in entry.parent_shas:
            if sha not in fpl_shas:
                analysis_stack[sha] = full_map[sha]
            else:
                fpl_branch_off_shas.append(sha)

    # find the relevant first parent range and append these to the
    # list of lin_log
    start_index = fpl_shas.index(start_sha)
    end_index = max(
        list(map(lambda x: fpl_shas.index(x), fpl_branch_off_shas)))

    for sha in fpl_shas[start_index:(end_index+1)]:
        analysis_lin_log[sha] = full_map[sha]

    # purge all parent shas from the lin_log that are not part of the
    # sub log that was extracted
    for entry in analysis_lin_log.values():
        entry.parent_shas = list(
            filter(lambda x: x in analysis_lin_log, entry.parent_shas))

    return list(analysis_lin_log.values())


def _collapse_linear_logs_step(lin_log):
    full_map = {x.sha: x for x in lin_log}

    # find the reference counts
    ref_count = {}
    for entry in lin_log:
        for sha in entry.parent_shas:
            new_count = ref_count.get(sha, 0) + 1
            ref_count[sha] = new_count

    # shorten all paths that just have one parent
    for ei, entry in enumerate(lin_log):
        p_shas = entry.parent_shas

        for index, sha in enumerate(p_shas):
            sha_p_shas = full_map[sha].parent_shas

            # while condition
            # - the ref count must be one
            # - it must not be a merge commit
            # - current sha must not be the parent sha
            # --> if all true linear log can be shortened
            while ref_count[sha] == 1 and len(sha_p_shas) == 1 and sha != sha_p_shas[0]:
                sha = sha_p_shas[0]

            p_shas[index] = sha

        entry.parent_shas = p_shas

    return extract_sparse_lin_log(lin_log, lin_log[0].sha)


def collapse_linear_logs(lin_log):
    """Given a linear log a lot of linear
       logs e.g.
       A <-- B <-- C <-- D
       can be shortened to
       A <-- D
       This can be used to reduce the number of
       log items thus extracting the actual branching structure

       Branch off points and merge commits are not collapsed

    Args:
        lin_log (List[ChangeLogEntry]): Linear Log

    Returns:
        List[ChangeLogEntry]: Collapsed Linear Log
    """
    do_continue = True

    while do_continue:
        len_before = len(lin_log)
        lin_log = _collapse_linear_logs_step(lin_log)
        len_after = len(lin_log)

        do_continue = len_before != len_after

    return lin_log


def extract_sparse_hier_log(lin_log, start_sha):
    """Extract Sparse Hierarchy Log from linear log
       Given a linear log and a start merge commit
       this function will extract the hierarchy log
       containig all linear first parent log until all
       branch off points.

    Args:
        lin_log (List[ChangeLogEntry]): Linear Log
        start_sha (str): Start sha

    Returns:
        List[ChangeLogEntry]: Hiearchy Log
    """
    sparse_lin_log = extract_sparse_lin_log(lin_log, start_sha)
    sparse_lin_log = collapse_linear_logs(sparse_lin_log)
    return linear_log_to_hierarchy_log(sparse_lin_log)
