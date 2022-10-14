import os
import subprocess


class GitError(Exception):
    pass


def exec_sub_process(args, verbose):
    process = subprocess.Popen(
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
    def __init__(self, remote, local, verbose=False):
        self.remote = remote
        self.local = local
        self.verbose = verbose
        self.local_git = os.path.join(self.local, '.git')
        self._clone_if_required()

    def _clone_if_required(self):
        if os.path.isdir(self.local):
            return

        return exec_sub_process([
            "git",
            "clone",
            self.remote,
            self.local,
        ], self.verbose)

    def _execute_git_cmd(self, *args):
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
        return self._execute_git_cmd("fetch", "--tags", "--force")

    def rev_parse(self, *args):
        if not args:
            args = ['HEAD']

        return self._execute_git_cmd("rev-parse", *args)

    def remotes(self):
        return self._execute_git_cmd_split_strip("remote")

    def local_branch_names(self):
        local_branches = self._execute_git_cmd_split_strip("branch")
        local_branches = list(
            map(lambda x: x.replace('* ', ''), local_branches))
        return local_branches

    def remote_branch_names(self):
        remotes = self.remotes()
        remote_branches = self._execute_git_cmd_split_strip("branch", "-r")

        for remote in remotes:
            remote_branches = list(
                map(lambda x: x.replace(f'{remote}/HEAD -> ', ''), remote_branches))

        return remote_branches

    def tags(self):
        return self._execute_git_cmd_split_strip("tag", "-l")
