from unittest import TestCase
from gitaudit.github.graphql_objects import PullRequest

import os
import json


ASSETS_ROOT = os.path.join(os.path.dirname(__file__), 'assets')


class TestGraphQlObjects(TestCase):
    def test_pull_request(self):
        fp = os.path.join(ASSETS_ROOT, 'json_ret_pull_request.json')
        with open(fp, 'r') as f:
            json_data = json.load(f)

        PullRequest.parse_obj(json_data)
