"""Class that communicated with local git installation."""

import os
import subprocess


class GitError(Exception):
    """Generic git error for exceptions raised by the git class."""


def exec_sub_process(args: "list[str]", verbose: "bool") -> "tuple(str, str)":
    """Executes Subprocess Popen call and stores the communication
    and stores communication of output and error

    Args:
        args (list[str]): arguments as list of strings
        verbose (bool): whether the output shall be
            printed to the console

    Raises:
        GitError: In case git returns an error output a GitError
            is raised with the message

    Returns:
        str: Git output as text decoded to utf-8 and stripped
            from leading and trailing whitespace
    """
    process = subprocess.Popen(  # pylint: disable=consider-using-with
        args=args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, err = process.communicate()

    output = output.decode("utf-8").strip()
    err = err.decode("utf-8").strip()

    if verbose:
        print(output)

    if err:
        raise GitError(err)

    return output


class Git:
    """Class that communicated with local git installation.
    """

    def __init__(self, remote: "str", local: "str", verbose: "bool" = False):
        self.remote = remote
        self.local = local
        self.verbose = verbose
        self.local_git = os.path.join(self.local, '.git')
        self._clone_if_required()

    def _clone_if_required(self):
        if os.path.isdir(self.local):
            return

        exec_sub_process([
            "git",
            "clone",
            self.remote,
            self.local,
        ], self.verbose)

    def _execute_git_cmd(self, *args: "list[str]"):
        full_args = [
            "git",
            f'--git-dir={self.local_git}',
            f'--work-tree={self.local}',
        ] + list(args)
        return exec_sub_process(full_args, self.verbose)

    def _execute_git_cmd_split_strip(self, *args):
        return list(map(lambda x: x.strip(), (
            self._execute_git_cmd(*args)
            .split("\n")
        )))

    def fetch(self):
        """Fetch the repository. Will also fetch all tags
        and force override of local remote branches if they have
        been rebased on the remote.

        Returns:
            str: git output of the fetch command
        """
        return self._execute_git_cmd("fetch", "--tags", "--force")

    def rev_parse(self, *args: "list[str]"):
        """Execute rev parse. By default will execute "git rev-parse HEAD"

        Args:
            *args (List(str)): Arguments to rev-parse command. Default HEAD

        Returns:
            str: Rev-parse output
        """
        if not args:
            args = ['HEAD']

        return self._execute_git_cmd("rev-parse", *args)

    def remotes(self):
        """Returns remotes as list of strings

        Returns:
            List(str): Remotes of the repository
        """
        return self._execute_git_cmd_split_strip("remote")

    def local_branch_names(self):
        """Returns list of local branch names.

        Returns:
            List(str): List of locally checked out branches.
        """
        local_branches = self._execute_git_cmd_split_strip("branch")
        local_branches = list(
            map(lambda x: x.replace('* ', ''), local_branches))
        return local_branches

    def remote_branch_names(self):
        """Returns list of remote branches including remote name
        (e.g. <remote>/<branch_name>)

        Returns:
            List(str): List of branches across all remotes
        """
        remotes = self.remotes()
        remote_branches = self._execute_git_cmd_split_strip("branch", "-r")

        for remote in remotes:
            repl_text = f'{remote}/HEAD -> '
            remote_branches = list(map(
                lambda x: x.replace(
                    repl_text, ''),  # pylint: disable=cell-var-from-loop
                remote_branches,
            ))

        return remote_branches

    def tags(self):
        """Returns list of tags

        Returns:
            List(str): List of tags checked out locally
        """
        return self._execute_git_cmd_split_strip("tag", "-l")
