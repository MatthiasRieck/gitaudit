from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.analysis.merge_debt.buckets import BucketList


class TestBucketList(TestCase):
    def test_prune_single_child_and_second_after(self):
        hier_log = ChangeLogEntry.list_from_objects([{
            "sha": "a",
            "parent_shas": ["b", "c"],
            "other_parents": [[
                {
                    "sha": "c",
                    "parent_shas": ["d"]
                },
                {
                    "sha": "d",
                    "parent_shas": [],
                }
            ]]
        }])

        bucket_list = BucketList(hier_log)
        bucket_list.prune_sha('c')
        self.assertListEqual(
            bucket_list.entries[0].branch_shas,
            ['d'],
        )
        bucket_list.prune_sha('d')
        self.assertListEqual(
            bucket_list.entries,
            []
        )

    def test_prune_merge_commit(self):
        hier_log = ChangeLogEntry.list_from_objects([{
            "sha": "a",
            "parent_shas": ["b", "c"],
            "other_parents": [[
                {
                    "sha": "c",
                    "parent_shas": ["d"]
                },
                {
                    "sha": "d",
                    "parent_shas": [],
                }
            ]]
        }])

        bucket_list = BucketList(hier_log)

        bucket_list.prune_sha('a')
        self.assertListEqual(
            bucket_list.entries,
            []
        )

    def test_prune_sub_child(self):
        hier_log = ChangeLogEntry.list_from_objects([{
            "sha": "a",
            "parent_shas": ["b", "c"],
            "other_parents": [[
                {
                    "sha": "c",
                    "parent_shas": ["d", "e"],
                    "other_parents": [[
                        {
                            "sha": "e",
                            "parent_shas": []
                        }
                    ]]
                },
                {
                    "sha": "d",
                    "parent_shas": [],
                }
            ]]
        }])

        bucket_list = BucketList(hier_log)

        bucket_list.prune_sha('e')
        self.assertListEqual(
            bucket_list.entries[0].children_shas,
            ["c"]
        )
        self.assertListEqual(
            bucket_list.entries[0].children[0].children_shas,
            [],
        )
        self.assertListEqual(
            bucket_list.entries[0].children[0].branch_shas,
            ["d"],
        )

        bucket_list.prune_sha('d')

        self.assertListEqual(
            bucket_list.entries,
            []
        )

    def test_prune_hierarchy(self):
        hier_log = ChangeLogEntry.list_from_objects([{
            "sha": "a",
            "parent_shas": ["b", "c"],
            "other_parents": [[
                {
                    "sha": "c",
                    "parent_shas": ["d", "e"],
                    "other_parents": [[
                        {
                            "sha": "e",
                            "parent_shas": ["f", "1"],
                            "other_parents": [[
                                {
                                    "sha": "1",
                                    "parent_shas": []
                                }
                            ]]
                        },
                        {
                            "sha": "f",
                            "parent_shas": []
                        }
                    ]]
                },
                {
                    "sha": "d",
                    "parent_shas": [],
                }
            ]]
        }, {
            "sha": "b",
            "parent_shas": []
        }])

        bucket_list = BucketList(hier_log)

        bucket_list.prune_sha("e")
        self.assertListEqual(
            bucket_list.entries[0].children_shas,
            ["c"]
        )
        self.assertListEqual(
            bucket_list.entries[0].children[0].children_shas,
            [],
        )
        self.assertListEqual(
            bucket_list.entries[0].children[0].branch_shas,
            ["d"],
        )

        # prune something that is no longer in entries
        bucket_list.prune_sha("1")
        self.assertListEqual(
            bucket_list.entries[0].children_shas,
            ["c"]
        )
        self.assertListEqual(
            bucket_list.entries[0].children[0].children_shas,
            [],
        )
        self.assertListEqual(
            bucket_list.entries[0].children[0].branch_shas,
            ["d"],
        )
