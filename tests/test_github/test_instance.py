from unittest import TestCase
from unittest.mock import patch

from gitaudit.github.instance import Github
from gitaudit.github.graphql_objects import PullRequest

import os
import json


ASSETS_ROOT = os.path.join(os.path.dirname(__file__), 'assets')
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

    def test_mutation(self):
        self.session_mock.append_success_post({'data': 'success'})
        github = Github(token="dummy")

        res = github.mutation('testmutation')

        self.assertEqual(res, 'success')
        self.assert_github_called_with_args_list(
            {"url": GQL_URL, "json": {"query": r'mutation {testmutation}'}}
        )

    def test_pull_request(self):
        fp = os.path.join(ASSETS_ROOT, 'json_ret_pull_request.json')
        with open(fp, 'r') as f:
            json_data = json.load(f)

        self.session_mock.append_success_post({
            'data': {
                'repository': {
                    'pullRequest': json_data
                }
            }
        })
        github = Github(token="dummy")

        res = github.pull_request('python', 'cpython', 98604, 'dummy')
        ref = PullRequest.parse_obj(json_data)

        self.assertEqual(res, ref)
        self.assert_github_called_with_args_list(
            {
                "url": GQL_URL,
                "json": {
                    "query": 'query {repository(owner:"python", name:"cpython"){ pullRequest(number:98604) { dummy } }}',  # noqa: E501
                }
            }
        )

    def test_add_comment(self):
        self.session_mock.append_success_post({
            'data': 'success'
        })
        github = Github(token="dummy")

        github.add_comment('dummyid', 'dummybody')
        self.assert_github_called_with_args_list(
            {
                "url": GQL_URL,
                "json": {
                    "query": 'mutation {addComment(input: {body: "dummybody", subjectId: "dummyid"}){ clientMutationId }}',  # noqa: E501
                }
            }
        )
