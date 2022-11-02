from unittest import TestCase
from gitaudit.branch.sparse_hierarchy import extract_sparse_hier_log
from gitaudit.git.change_log_entry import ChangeLogEntry


class TestUtils(TestCase):
    def test_sparse_extract(self):
        EXAMPLE_C = [
            "a[b f]",
            "b[d c]",
            "d[e]",
            "c[d]",
            "e[1]",
            "1[]",
            "f[2 4]",
            "2[3]",
            "3[1]",
            "4[5]",
            "5[3]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        lin_log_cpy = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        hier_log = extract_sparse_hier_log(lin_log, 'a')
