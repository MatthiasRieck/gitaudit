from unittest import TestCase
from unittest.mock import patch

from gitaudit.git.controller import Git


class ProcessMock:
    def __init__(self):
        self.return_data = []

    def append_communicate(self, output, err):
        self.return_data.append((output.encode('utf-8'), err.encode('utf-8')))

    def communicate(self):
        return self.return_data.pop(0)


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
        self.assert_git_called_with_args('fetch', '--tags', '--force')

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