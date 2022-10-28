"""Github communication instance"""

import netrc
import requests

from .graphql_objects import PullRequest


class Github:
    """Instance communicating with Github"""

    def __init__(self, url: str = "https://api.github.com/graphql", token: str = ""):
        self.url = url

        if token:
            self.token = token
        else:
            self.token = netrc.netrc().authenticators(url)[2]

        self.session = requests.Session()
        self.session.headers = {
            "Authorization": f"token {self.token}",
            "Content-type": "application/json; charset=utf-8;",
            "Accept": "application/json;",
        }

    def _call(self, data: str):
        response = self.session.post(url=self.url, json={"query": data})
        return response.json()["data"]

    def query(self, querydata: str):
        """Call Github using a query

        Args:
            querydata (str): GraphQl Query

        Returns:
            dict: Json return object
        """
        return self._call(f"query {{{querydata}}}")

    def mutation(self, mutationdata):
        """Call Github using a query

        Args:
            mutationdata (str): GraphQl mutation

        Returns:
            dict: Json return object
        """
        return self._call(f"mutation {{{mutationdata}}}")

    def pull_request(self, owner: str, repo: str, number: int, querydata: str):
        """Queries Pull Request Information

        Args:
            owner (str): The owner of the repository
            repo (str): The repository name
            number (int): The pull request number
            query (str): The requested GraphQL query data

        Returns:
            PullRequest: The pull request object
        """
        res = self.query(f"""
            repository(owner:"{owner}", name:"{repo}") {{
                pullRequest(number:{number}) {{ {querydata} }}
        }}""")
        return PullRequest.parse_obj(res['repository']['pullRequest'])
