from unittest import TestCase
from unittest.mock import patch

from datetime import datetime
from io import BytesIO

from gitaudit.git.controller import Git
from gitaudit.git.change_log_entry import ChangeLogEntry, FileAdditionsDeletions

from .test_change_log_entry import LOG_ENTRY_HEAD, LOG_ENTRY_NO_PARENT


class ProcessMock:
    def __init__(self):
        self.return_data = []

    def append_communicate(self, output, err):
        self.return_data.append((output.encode('utf-8'), err.encode('utf-8')))

    def communicate(self):
        return self.return_data.pop(0)

    @property
    def stdout(self):
        return BytesIO(self.return_data.pop(0)[0])

    @property
    def stderr(self):
        return BytesIO("".encode('utf-8'))


class TestGit(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mock_check_call_patchr = patch("subprocess.Popen")
        cls.mock_check_call = cls.mock_check_call_patchr.start()

        cls.process_mock = ProcessMock()
        cls.mock_check_call.return_value = cls.process_mock

        cls.mock_is_dir_patchr = patch('os.path.isdir')
        cls.mock_is_dir = cls.mock_is_dir_patchr.start()
        cls.mock_is_dir.return_value = True

    @classmethod
    def tearDownClass(cls):
        cls.mock_check_call_patchr.stop()
        cls.mock_is_dir_patchr.stop()
        super().tearDownClass()

    @classmethod
    def append_process_return_text(cls, output='', err=''):
        cls.process_mock.append_communicate(output, err)

    def assert_git_called_with_args_list(self, *expected_args_list):
        called_args_list = \
            self.mock_check_call.call_args_list[-len(expected_args_list):]
        for called_args, expected_args in zip(called_args_list, expected_args_list):
            self.assertListEqual(
                called_args[1]['args'][3:],
                expected_args,
            )

    def assert_git_called_with_args(self, *expected_args):
        self.assert_git_called_with_args_list(list(expected_args))

    def test_fetch(self):
        self.append_process_return_text()
        Git('', '').fetch()
        self.assert_git_called_with_args('fetch', '--tags', '--force', '-q')

    def test_rev_parse(self):
        self.append_process_return_text(
            output='b708ae022bf174d9c4f4dde557d45643b935275c',
        )
        self.append_process_return_text(
            output='cd8c9ebdade2a02630cf9beb370d22a821c25101',
        )

        # call with default = HEAD
        self.assertEqual(
            Git('', '').rev_parse(),
            'b708ae022bf174d9c4f4dde557d45643b935275c',
        )
        self.assert_git_called_with_args('rev-parse', 'HEAD')

        # call with certain branch
        self.assertEqual(
            Git('', '').rev_parse('master'),
            'cd8c9ebdade2a02630cf9beb370d22a821c25101',
        )
        self.assert_git_called_with_args('rev-parse', 'master')

    def test_remotes(self):
        self.append_process_return_text('origin\nupstream')
        self.assertListEqual(
            Git('', '').remotes(),
            ['origin', 'upstream'],
        )
        self.assert_git_called_with_args('remote')

    def test_local_branch_names(self):
        self.append_process_return_text('main\ndev\nfeature')
        self.assertListEqual(
            Git('', '').local_branch_names(),
            ['main', 'dev', 'feature'],
        )
        self.assert_git_called_with_args('branch')

    def test_remote_branch_names(self):
        self.append_process_return_text('upstream')
        self.append_process_return_text(
            'upstream/HEAD -> upstream/dev\nupstream/main'
        )
        self.assertListEqual(
            Git('', '').remote_branch_names(),
            ['upstream/dev', 'upstream/main'],
        )
        # self.assert_git_called_with_args('branch')

        self.assert_git_called_with_args_list(
            ['remote'],
            ['branch', '-r'],
        )

    def test_tags(self):
        self.append_process_return_text('main\ndev\nfeature')
        self.assertListEqual(
            Git('', '').tags(),
            ['main', 'dev', 'feature'],
        )
        self.assert_git_called_with_args('tag', '-l')

    def test_log(self):
        self.append_process_return_text(
            '27686336213\n12876371637123\n217283671623')
        self.assertListEqual(
            Git('', '').log(pretty='%H', end_ref='main').split('\n'),
            ['27686336213', '12876371637123', '217283671623'],
        )
        self.assert_git_called_with_args(
            '--no-pager', 'log', '--pretty=%H', 'main'
        )

    def test_log_parentlog(self):
        self.append_process_return_text(
            'c[b]\nb[a]\na[]'
        )
        self.assertListEqual(
            Git('', '').log_parentlog(end_ref='main'),
            [
                ChangeLogEntry(sha='c', parent_shas=['b']),
                ChangeLogEntry(sha='b', parent_shas=['a']),
                ChangeLogEntry(sha='a', parent_shas=[]),
            ],
        )
        self.assert_git_called_with_args(
            '--no-pager', 'log', '--pretty=%H[%P](%cI)', 'main'
        )

    def test_log_start_sha(self):
        self.append_process_return_text(
            'c[b]\nb[a]\na[]'
        )
        self.assertListEqual(
            Git('', '').log_parentlog(end_ref='main', start_ref='dummyref'),
            [
                ChangeLogEntry(sha='c', parent_shas=['b']),
                ChangeLogEntry(sha='b', parent_shas=['a']),
                ChangeLogEntry(sha='a', parent_shas=[]),
            ],
        )
        self.assert_git_called_with_args(
            '--no-pager', 'log', '--pretty=%H[%P](%cI)', 'dummyref...main'
        )

    def test_log_changelog(self):
        self.append_process_return_text(
            "#CS#\n"+LOG_ENTRY_HEAD+"\n#CS#\n"+LOG_ENTRY_NO_PARENT
        )
        changelog = Git('', '').log_changelog(end_ref='main')

        self.assertListEqual(
            list(map(lambda x: x.sha, changelog)),
            [
                "b74c293300e1afcec19c44369fc9cdc2236b2ee4",
                "8d0be78827d398c01bc8288d7a381f5402fb1931",
            ],
        )
        self.assert_git_called_with_args(
            '--no-pager', 'log', (
                r"--pretty=#CS#%n"
                r"H:[%H]%nP:[%P]%nT:[%D]%nS:[%s]%nD:[%cI]%nA:[%an]%nM:[%ae]%n"
                r"#SB#%n%b%n#EB#%n"
            ), '--submodule=diff', 'main', "-m", "--numstat"
        )

    def test_show(self):
        self.append_process_return_text(
            '27686336213'
        )
        self.assertEqual(
            Git('', '').show(pretty='%H', ref='main'),
            '27686336213',
        )
        self.assert_git_called_with_args(
            'show', '--pretty=%H', 'main'
        )

    def test_show_parentlog_entry(self):
        self.append_process_return_text(
            'b[a]'
        )
        self.assertEqual(
            Git('', '').show_parentlog_entry(ref='b'),
            ChangeLogEntry(sha='b', parent_shas=['a']),
        )
        self.assert_git_called_with_args(
            'show', '--pretty=%H[%P](%cI)', 'b'
        )

    def test_show_changelog_entry(self):
        self.append_process_return_text(
            LOG_ENTRY_HEAD
        )
        self.assertEqual(
            Git('', '').show_changelog_entry(ref='main'),
            ChangeLogEntry(
                sha='b74c293300e1afcec19c44369fc9cdc2236b2ee4',
                parent_shas=['73ee81321f193db02a452d3f122b10bcd92bec17'],
                refs=['git-log'],
                subject='numstat without patch',
                commit_date=datetime.fromisoformat(
                    '2022-10-18T21:02:44+02:00'),
                author_name='Dummy Name',
                author_mail='Dummy.Name@domain.com',
                numstat=[FileAdditionsDeletions(
                    path='gitaudit/git/controller.py',
                    additions=4,
                    deletions=3,
                )],
            )
        )
