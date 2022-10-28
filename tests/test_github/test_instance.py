from unittest import TestCase
from unittest.mock import patch

from gitaudit.github.instance import Github


GQL_URL = "https://api.github.com/graphql"


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class SessionMock:
    def __init__(self) -> None:
        self.return_data = []
        self.post_call_args = []
        self.headers = None

    def append_success_post(self, json_data):
        self.return_data.append(MockResponse(
            json_data=json_data,
            status_code=200,
        ))

    def post(self, **kwargs):
        self.post_call_args.append(kwargs)
        return self.return_data.pop(0)


class TestGithub(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.mock_session_patchr = patch('requests.Session')
        cls.mock_session = cls.mock_session_patchr.start()

        cls.session_mock = SessionMock()
        cls.mock_session.return_value = cls.session_mock

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mock_session_patchr.stop()
        super().tearDownClass()

    def assert_github_called_with_args_list(self, *expected_args_list):
        called_args_list = \
            self.session_mock.post_call_args[-len(expected_args_list):]

        for called_args, expected_args in zip(called_args_list, expected_args_list):
            self.assertDictEqual(
                called_args,
                expected_args,
            )

    def test_query(self):
        self.session_mock.append_success_post({'data': 'success'})
        github = Github(token="dummy")

        res = github.query('testquery')

        self.assertEqual(res, 'success')
        self.assert_github_called_with_args_list(
            {"url": GQL_URL, "json": {"query": r'query {testquery}'}}
        )
