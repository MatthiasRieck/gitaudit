"""Class that communicated with local git installation."""

import os
from typing import List
import subprocess
import io
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

    output = output.decode(encoding="utf-8", errors="ignore").strip()
    err = err.decode("utf-8").strip()

    if verbose:
        print(output)

    if err:
        raise GitError(err)

    return output


def exec_sub_process_yield(args: List[str], verbose: bool) -> str:
    """Executes Subprocess Popen call and stores the communication
    and yields the output line by line

    Args:
        args (list[str]): arguments as list of strings
        verbose (bool): whether the output shall be
            printed to the console

    Raises:
        GitError: In case git returns an error output a GitError
            is raised with the message

    Returns:
        str: Git output as text yielded line by line and decoded to utf-8 and stripped
            from leading and trailing whitespace
    """
    process = subprocess.Popen(  # pylint: disable=consider-using-with
        args=args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # output, err = process.communicate()

    for line in io.TextIOWrapper(process.stdout, encoding="utf-8", errors='ignore'):
        if verbose:
            print(line)
        yield line

    err = process.stderr.read()

    if err:
        raise GitError(err)


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

    def _execute_git_cmd_yield(self, *args: "list[str]"):
        full_args = [
            "git",
            f'--git-dir={self.local_git}',
            f'--work-tree={self.local}',
        ] + list(args)
        for line in exec_sub_process_yield(full_args, self.verbose):
            yield line

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
        return self._execute_git_cmd("fetch", "--tags", "--force", "-q", "--no-recurse-submodules")

    def gc(self, *options):  # pylint: disable=invalid-name
        """Cleanup unnecessary files and update the local repository
        """
        self._execute_git_cmd("gc", *options)

    def pull(self):
        """Execute git pull
        """
        self._execute_git_cmd("pull", "--no-recurse-submodules")

    def checkout(self, ref: str, create_branch: bool = False):
        """Git checkout ref

        Args:
            ref (str): Ref (Branch / Tag / Sha)
        """
        args = ["checkout", "--no-recurse-submodules"]

        if create_branch:
            args.append("-b")

        self._execute_git_cmd(*args, ref)

    def push(self, branch_name: str, remote="origin"):
        """Execute Git Push

        Args:
            branch_name (str): Name of the branch
            remote (str, optional): Name of the remote. Defaults to "origin".
        """
        self._execute_git_cmd("push", remote, f"{branch_name}:{branch_name}")

    def add(self, path: str):
        """Execute git add

        Args:
            path (str): the path to the file to the staged (relative).
                "." for all.
        """
        self._execute_git_cmd("add", path)

    def commit(self, subject: str, body: str = None, allow_empty: bool = False):
        """Execute Git Commit

        Args:
            subject (str): Subject / Title / Headline of the commit
            body (str, optional): The body of the commit message. Defaults to None.
            allow_empty (bool, optional): Set true if empty commits shall be allowed.
                Defaults to False.
        """
        args = []
        if allow_empty:
            args.append("--allow-empty")
        args.extend(["-m", subject])
        if body:
            args.extend(["-m", body])

        self._execute_git_cmd("commit", *args)

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
        return "".join(self._yield_line_log(
            pretty=pretty,
            end_ref=end_ref,
            start_ref=start_ref,
            first_parent=first_parent,
            submodule=submodule,
            patch=patch,
            other=other,
        ))

    def _yield_line_log(  # pylint: disable=too-many-arguments
        self,
        pretty,
        end_ref, start_ref=None,
        first_parent=False,
        submodule=None,
        patch=False,
        other=None,
    ):
        args = [
            "--no-pager",
            "log",
            f"--pretty={pretty}",
            "--first-parent" if first_parent else None,
            f"--submodule={submodule}" if submodule else None,
            "-p" if patch else None,
            f"{start_ref}...{end_ref}" if start_ref else end_ref,
        ] + (other if other else [])
        args = list(filter(lambda x: x is not None, args))

        for line in self._execute_git_cmd_yield(*args):
            yield line

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

    def log_changelog(self, end_ref, start_ref=None, first_parent=False, patch=False):
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

        entries = []
        collect_lines = []

        for line in self._yield_line_log(
            pretty=pretty,
            end_ref=end_ref,
            start_ref=start_ref,
            submodule="diff",
            other=["-m", "--numstat"],
            patch=patch,
            first_parent=first_parent,
        ):
            if line == '#CS#\n':
                if collect_lines:
                    entries.append(ChangeLogEntry.from_log_text(
                        "".join(collect_lines)
                    ))

                collect_lines = []
            else:
                collect_lines.append(line)

        if collect_lines:
            entries.append(ChangeLogEntry.from_log_text(
                "".join(collect_lines)
            ))

        return entries

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

    def log_parentlog(self, end_ref, start_ref=None):
        """Given an end_ref this function
        will return ChangeLogEntry list (linear log)
        with sha and parent shas which can
        be used to construct a hierarchy log

        Args:
            end_ref (str): End Ref
            start_ref(str): Start Ref

        Returns:
            List[ChangeLogEntry]: Linear ChangeLogEntry log
        """

        entries = []

        for line in self._yield_line_log(
            pretty=r"%H[%P](%cI)",
            end_ref=end_ref,
            start_ref=start_ref,
        ):
            entries.append(ChangeLogEntry.from_head_log_text(line))

        return entries

    def show_parentlog_entry(self, ref):
        """Show parent log entry information

        Args:
            ref (str): Ref (branch, tag, sha)

        Returns:
            ChangeLogEntry: change log entry with parent
                information
        """
        log_text = self.show(
            pretty=r"%H[%P](%cI)",
            ref=ref,
        )
        return ChangeLogEntry.from_head_log_text(log_text)
