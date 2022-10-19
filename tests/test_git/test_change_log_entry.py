from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
import pytz
from datetime import datetime

LOG_ENTRY_HEAD = """
H:[b74c293300e1afcec19c44369fc9cdc2236b2ee4]
P:[73ee81321f193db02a452d3f122b10bcd92bec17]
T:[HEAD -> git-log]
S:[numstat without patch]
D:[2022-10-18T21:02:44+02:00]
A:[Dummy Name]
M:[Dummy.Name@domain.com]
#SB#

#EB#


4	3	gitaudit/git/controller.py
""".strip()

LOG_ENTRY_NO_PARENT = """
H:[8d0be78827d398c01bc8288d7a381f5402fb1931]
P:[]
T:[]
S:[Initial commit]
D:[2022-10-13T07:44:04+02:00]
A:[Dummy Name]
M:[Dummy.Name@domain.com]
#SB#

#EB#


129	0	.gitignore
21	0	LICENSE
1	0	README.md
""".strip()

LOG_ENTRY_TAGS = """
H:[cd8c9ebdade2a02630cf9beb370d22a821c25101]
P:[53f3875dfe189e1d5c59d60129a011c3c4ae8b60 0c71bc7d2bcf1b357f033ffbbf14b8c3468a82dc]
T:[tag: dummtag, tag: 0.0.2]
S:[Merge pull request #5 from MatthiasRieck/bugfix_deploy]
D:[2022-10-13T08:16:03+02:00]
A:[Dummy Name]
M:[Dummy.Name@domain.com]
#SB#
Update setup.py
#EB#


1	1	setup.py
""".strip()

LOG_ENTRY_REFS = """
H:[3569a40a800958a1fddf91eef1f34652c929cb7e]
P:[fb4e81792b6558492adf099d717d1a73286900a3 2014379722f66ecfe1b81edc04b397258815c6f0]
T:[origin/main, origin/HEAD, main]
S:[Merge pull request #9 from MatthiasRieck/pytest-cov]
D:[2022-10-16T19:44:10+02:00]
A:[Dummy Name]
M:[Dummy.Name@domain.com]
#SB#
Pytest Coverage
#EB#


9	3	.github/workflows/python-package.yml
70	10	gitaudit/git/controller.py
14	7	setup.py
2	0	test-requirements.txt
""".strip()


class TestChangeLogEntry(TestCase):
    def test_log_entry_head(self):
        entry = ChangeLogEntry.from_log_text(LOG_ENTRY_HEAD)
        self.assertEqual(entry.sha, 'b74c293300e1afcec19c44369fc9cdc2236b2ee4')
        self.assertListEqual(entry.parent_shas, [
                             '73ee81321f193db02a452d3f122b10bcd92bec17'])
        self.assertListEqual(entry.tags, [])
        self.assertListEqual(entry.refs, ['git-log'])
        self.assertEqual(entry.subject, 'numstat without patch')
        self.assertEqual(entry.commit_date, datetime(
            2022, 10, 18, 19, 2, 44, tzinfo=pytz.utc))
        self.assertEqual(entry.author_name, 'Dummy Name')
        self.assertEqual(entry.author_mail, 'Dummy.Name@domain.com')
        self.assertEqual(entry.body, '')

        self.assertEqual(entry.numstat[0].additions, 4)
        self.assertEqual(entry.numstat[0].deletions, 3)
        self.assertEqual(entry.numstat[0].path, "gitaudit/git/controller.py")

    def test_no_parents_initial_commit(self):
        entry = ChangeLogEntry.from_log_text(LOG_ENTRY_NO_PARENT)
        self.assertEqual(entry.sha, '8d0be78827d398c01bc8288d7a381f5402fb1931')
        self.assertListEqual(entry.parent_shas, [])
        self.assertListEqual(entry.tags, [])
        self.assertListEqual(entry.refs, [])
        self.assertEqual(entry.subject, 'Initial commit')
        self.assertEqual(entry.commit_date, datetime(
            2022, 10, 13, 5, 44, 4, tzinfo=pytz.utc))
        self.assertEqual(entry.author_name, 'Dummy Name')
        self.assertEqual(entry.author_mail, 'Dummy.Name@domain.com')
        self.assertEqual(entry.body, '')

        self.assertEqual(entry.numstat[0].additions, 129)
        self.assertEqual(entry.numstat[0].deletions, 0)
        self.assertEqual(entry.numstat[0].path, ".gitignore")

        self.assertEqual(entry.numstat[1].additions, 21)
        self.assertEqual(entry.numstat[1].deletions, 0)
        self.assertEqual(entry.numstat[1].path, "LICENSE")

        self.assertEqual(entry.numstat[2].additions, 1)
        self.assertEqual(entry.numstat[2].deletions, 0)
        self.assertEqual(entry.numstat[2].path, "README.md")

    def test_tags(self):
        entry = ChangeLogEntry.from_log_text(LOG_ENTRY_TAGS)
        self.assertEqual(entry.sha, 'cd8c9ebdade2a02630cf9beb370d22a821c25101')
        self.assertListEqual(entry.parent_shas, [
                             '53f3875dfe189e1d5c59d60129a011c3c4ae8b60', '0c71bc7d2bcf1b357f033ffbbf14b8c3468a82dc'])
        self.assertListEqual(entry.tags, ['dummtag', '0.0.2'])
        self.assertListEqual(entry.refs, [])
        self.assertEqual(
            entry.subject, 'Merge pull request #5 from MatthiasRieck/bugfix_deploy')
        self.assertEqual(entry.commit_date, datetime(
            2022, 10, 13, 6, 16, 3, tzinfo=pytz.utc))
        self.assertEqual(entry.author_name, 'Dummy Name')
        self.assertEqual(entry.author_mail, 'Dummy.Name@domain.com')
        self.assertEqual(entry.body, 'Update setup.py')

    def test_refs(self):
        entry = ChangeLogEntry.from_log_text(LOG_ENTRY_REFS)
        self.assertEqual(entry.sha, '3569a40a800958a1fddf91eef1f34652c929cb7e')
        self.assertListEqual(entry.parent_shas, [
                             'fb4e81792b6558492adf099d717d1a73286900a3', '2014379722f66ecfe1b81edc04b397258815c6f0'])
        self.assertListEqual(entry.tags, [])
        self.assertListEqual(
            entry.refs, ['origin/main', 'origin/HEAD', 'main'])
        self.assertEqual(
            entry.subject, 'Merge pull request #9 from MatthiasRieck/pytest-cov')
        self.assertEqual(entry.commit_date, datetime(
            2022, 10, 16, 17, 44, 10, tzinfo=pytz.utc))
        self.assertEqual(entry.author_name, 'Dummy Name')
        self.assertEqual(entry.author_mail, 'Dummy.Name@domain.com')
        self.assertEqual(entry.body, 'Pytest Coverage')
