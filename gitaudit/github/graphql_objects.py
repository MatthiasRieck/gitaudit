"""Github GraphQL Objects"""

from __future__ import annotations

from typing import List, Optional
from pydantic import Field, root_validator
from .graphql_base import GraphQlBase


class Actor(GraphQlBase):
    """Represents an object which can
    take actions on GitHub. Typically a User or Bot."""
    login: Optional[str]


class Label(GraphQlBase):
    """A label for categorizing Issues, Pull Requests,
    Milestones, or Discussions with a given Repository."""
    name: Optional[str]
    color: Optional[str]
    id: Optional[str]


class Comment(GraphQlBase):
    """Represents a comment."""
    body: Optional[str]


class PullRequestReview(GraphQlBase):
    """A review object for a given pull request."""
    author: Optional[Actor]
    body: Optional[str]
    state: Optional[str]


class Commit(GraphQlBase):
    """Represents a Git commit."""
    oid: Optional[str]
    additions: Optional[str]
    deletions: Optional[str]
    message_body: Optional[str]
    message_headline: Optional[str]


class PullRequest(GraphQlBase):
    """A repository pull request."""
    author: Optional[Actor]
    number: Optional[int]
    comments: Optional[List[Comment]] = Field(default_factory=list)
    commits: Optional[List[Commit]] = Field(default_factory=list)
    labels: Optional[List[Label]]
    base_ref_name: Optional[str]
    head_ref_name: Optional[str]
    body: Optional[str]
    title: Optional[str]
    url: Optional[str]
    id: Optional[str]
    repository: Optional[Repository]
    reviews: Optional[List[PullRequestReview]]

    @root_validator(pre=True)
    def unwrap_commit(cls, data: dict):  # pylint: disable=no-self-argument
        """Unwraps commits

        Args:
            data (dict): The to be validated input data

        Returns:
            dict: The valiated and transformed input data
        """
        if 'commits' in data:
            data['commits'] = list(map(lambda x: x['commit'], data['commits']))
        return data


class Repository(GraphQlBase):
    """A repository contains the content for a project."""
    name: Optional[str]
    pull_requests: Optional[List[PullRequest]] = Field(
        default_factory=list)
    pull_request: Optional[PullRequest]


PullRequest.update_forward_refs()
