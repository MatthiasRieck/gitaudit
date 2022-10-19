"""Change Log Entry
"""

from typing import List
from datetime import datetime
import re
import pytz
from pydantic import BaseModel, Field


def extract_line_content(line, id_character):
    """Extracts the line content of git log with the format
    "<character>:[<content>]"

    Args:
        line (str): Line to be extracted from
        id_character (str): Single character for controll
            the extraction

    Returns:
        str: Returns the extracted content
    """
    matches = re.findall(
        r'(?<=^' + id_character + r':\[).*?(?=\]$)',
        line,
    )
    assert len(matches) == 1
    return matches[0]


def split_and_strip(text, splitby=','):
    """Split by character and strip each list element

    Args:
        text (str): Text to be split
        splitby (str, optional): character to be split by. Defaults to ','.

    Returns:
        List[str]: List of splitted and stripped strings
    """
    return list(filter(
        lambda x: x,
        map(
            lambda x: x.strip(),
            text.split(splitby),
        )
    ))


def extract_tags_refs(tag_line):
    """Extracts tags and refs from log line

    Args:
        tag_line (str): Line containing the tag and ref tags

    Returns:
        Tuple[List[str], List[str]]: List of tags and refs
    """
    line_content = extract_line_content(tag_line, 'T')
    refs = split_and_strip(line_content)
    tags = list(filter(lambda x: x.startswith('tag: '), refs))
    tags = list(map(lambda x: x[5:], tags))
    refs = list(filter(lambda x: not x.startswith('tag: '), refs))
    refs = list(map(lambda x: x.replace('HEAD -> ', ''), refs))

    return tags, refs


def extract_additions_deletions(numstat_text):
    """Extract additions and deletions from numstat text

    Args:
        numstat_text (str): Multiline text block containing the git
            log num stat information

    Returns:
        List[Dict[str, any]]: List of dictionaries
    """
    content = re.findall(r'(\d+)\t(\d+)\t(.+)', numstat_text)
    return list(map(lambda x: {
        "additions": int(x[0]),
        "deletions": int(x[1]),
        "path": x[2],
    }, content))


class FileAdditionsDeletions(BaseModel):
    """Dataclass for storing file additions and deletions
    """
    path: str
    additions: int
    deletions: int


class ChangeLogEntry(BaseModel):
    """Dataclass for storing change log data
    """
    sha: str
    parent_shas: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    refs: List[str] = Field(default_factory=list)
    subject: str
    commit_date: datetime
    author_name: str
    author_mail: str
    body: str = ''
    numstat: List[FileAdditionsDeletions] = Field(default_factory=list)

    @classmethod
    def from_log_text(cls, log_text):
        """Create ChangeLogEntry from logging text

        Args:
            log_text (str): Logging text

        Returns:
            ChangeLogEntry: Change log entry dataclass
        """
        item_text, rest_text = log_text.split('#SB#')
        body_text, numstat_text = rest_text.split('#EB#')

        (
            sha_line,
            parents_line,
            tags_line,
            subject_line,
            date_line,
            author_name_line,
            author_mail_line,
        ) = item_text.strip().split('\n')

        tags, refs = extract_tags_refs(tags_line)

        return ChangeLogEntry(
            sha=extract_line_content(sha_line, 'H'),
            parent_shas=split_and_strip(
                extract_line_content(parents_line, 'P'), splitby=' '),
            tags=tags,
            refs=refs,
            subject=extract_line_content(subject_line, 'S'),
            commit_date=datetime.fromisoformat(
                extract_line_content(date_line, 'D')).astimezone(pytz.utc),
            author_name=extract_line_content(author_name_line, 'A'),
            author_mail=extract_line_content(author_mail_line, 'M'),
            body=body_text.strip(),
            numstat=extract_additions_deletions(numstat_text),
        )