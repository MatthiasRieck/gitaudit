"""Class that communicated with local git installation."""

import os
import subprocess
from .change_log_entry import ChangeLogEntry


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

    output = output.decode("utf-8", "replace").strip()
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
            "-q",
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
        return self._execute_git_cmd("fetch", "--tags", "--force", "-q")

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
            remote_branches = [
                x.replace(repl_text, '') for x in remote_branches
            ]

        return remote_branches

    def tags(self):
        """Returns list of tags

        Returns:
            List(str): List of tags checked out locally
        """
        return self._execute_git_cmd_split_strip("tag", "-l")

    def log(  # pylint: disable=too-many-arguments
        self,
        pretty,
        end_ref, start_ref=None,
        first_parent=False,
        submodule=None,
        patch=False,
        other=None,
    ):
        """Execute git log

        Args:
            pretty (str): Pretty format
            end_ref (str): git reference where to start going backwards
            start_ref (str, optional): git reference where stop going backwards.
                Defaults to None.
            first_parent (bool, optional): If true git log only follows the
                first parent. Defaults to False.
            submodule (str, optional): Option for submodule diff. Defaults to None.
            patch (bool, optional): Enable patch output or not. Defaults to False.
            other (List[str], optional): Additional git log commands. Defaults to None.

        Returns:
            str: Git log as text
        """
        args = [
            "--no-pager",
            "log",
            f"--pretty={pretty}",
            "--first-parent" if first_parent else None,
            f"--submodule={submodule}" if submodule else None,
            "-p" if patch else None,
            f"{start_ref}..{end_ref}" if start_ref else end_ref,
        ] + (other if other else [])
        args = list(filter(lambda x: x is not None, args))

        output = self._execute_git_cmd(*args)
        return output

    def show(  # pylint: disable=too-many-arguments
        self,
        pretty,
        ref,
        submodule=None,
        patch=False,
        other=None,
    ):
        """Shows information for a single commit / ref

        Args:
            pretty (str): Pretty Text for Logging
            ref (str): Ref (branch, tag, sha)
            submodule (str, optional): How subodule changes are shown.
                Defaults to None.
            patch (bool, optional): Whether to show patch info.
                Defaults to False.
            other (List[str], optional): Additional arguments.
                Defaults to None.

        Returns:
            str: git show information as text
        """
        args = [
            "show",
            f"--pretty={pretty}",
            f"--submodule={submodule}" if submodule else None,
            "-p" if patch else None,
            ref,
        ] + (other if other else [])
        args = list(filter(lambda x: x is not None, args))

        output = self._execute_git_cmd(*args)
        return output

    def log_changelog(self, end_ref, start_ref=False, first_parent=False, patch=False):
        """Create changelog

        Args:
            end_ref (str): git reference where to start going backwards
            start_ref (str, optional): git reference where stop going backwards.
                Defaults to None.
            first_parent (bool, optional): If true git log only follows the
                first parent. Defaults to False.
            patch (bool, optional): _description_. Defaults to False.
            patch (bool, optional): Enable patch output or not. Defaults to False.

        Returns:
            List[ChangeLogEntry]: the changelog
        """
        pretty = (
            r"#CS#%n"
            r"H:[%H]%nP:[%P]%nT:[%D]%nS:[%s]%nD:[%cI]%nA:[%an]%nM:[%ae]%n"
            r"#SB#%n%b%n#EB#%n"
        )

        log_text = self.log(
            pretty=pretty,
            end_ref=end_ref,
            start_ref=start_ref,
            submodule="diff",
            other=["-m", "--numstat"],
            patch=patch,
            first_parent=first_parent,
        )

        return list(map(
            ChangeLogEntry.from_log_text,
            filter(lambda x: x, log_text.split('#CS#')),
        ))

    def show_changelog_entry(self, ref, patch=False):
        """Show single changelog entry

        Args:
            ref (str): Ref (branch, tag, sha)
            patch (bool, optional): Whether to show patch information.
                Defaults to False.

        Returns:
            ChangeLogEntry: change log entry
        """
        pretty = (
            r"H:[%H]%nP:[%P]%nT:[%D]%nS:[%s]%nD:[%cI]%nA:[%an]%nM:[%ae]%n"
            r"#SB#%n%b%n#EB#%n"
        )

        log_text = self.show(
            pretty=pretty,
            ref=ref,
            submodule="diff",
            other=["-m", "--numstat"],
            patch=patch,
        )

        return ChangeLogEntry.from_log_text(log_text)

    def log_parentlog(self, end_ref):
        """Given an end_ref this function
        will return ChangeLogEntry list (linear log)
        with sha and parent shas which can
        be used to construct a hierarchy log

        Args:
            end_ref (str): End Ref

        Returns:
            List[ChangeLogEntry]: Linear ChangeLogEntry log
        """
        log_text = self.log(
            pretty="%H[%P]",
            end_ref=end_ref,
        )
        return list(map(
            ChangeLogEntry.from_head_log_text,
            log_text.split("\n"),
        ))

    def show_parentlog_entry(self, ref):
        """Show parent log entry information

        Args:
            ref (str): Ref (branch, tag, sha)

        Returns:
            ChangeLogEntry: change log entry with parent
                information
        """
        log_text = self.show(
            pretty="%H[%P]",
            ref=ref,
        )
        return ChangeLogEntry.from_head_log_text(log_text)
