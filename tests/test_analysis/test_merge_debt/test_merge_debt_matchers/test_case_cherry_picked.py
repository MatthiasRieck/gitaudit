# 9db
#  | \
#  | 1e2
#  | /
# d91
#  | \
#  | a19
#  | /
# ad0
#  | \
#  | f07
#  | /
# 99f
#  | \
#  | 5ef
#  | /
# fd1
#  | \
#  | f0d
#  | /
# 48b
#  |
# 8d0
#  |
# a34


CHERRY_PICK_MAIN_LOG = [
    {
        "sha": "9db",
        "parent_shas": ["d91", "1e2"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "1e2",
        "parent_shas": ["d91"],
        "cherry_pick_sha": "431",
    },
    {
        "sha": "d91",
        "parent_shas": ["ad0", "a19"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "a19",
        "parent_shas": ["ad0"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "ad0",
        "parent_shas": ["99f", "f07"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "f07",
        "parent_shas": ["99f"],
        "cherry_pick_sha": "6b6",
    },
    {
        "sha": "99f",
        "parent_shas": ["fd1", "5ef"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "5ef",
        "parent_shas": ["fd1"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "fd1",
        "parent_shas": ["48b", "f0d"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "f0d",
        "parent_shas": ["48b"],
        "cherry_pick_sha": "b56",
    },
    {
        "sha": "48b",
        "parent_shas": ["8d0"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "8d0",
        "parent_shas": ["a34"],
        "cherry_pick_sha": "562",
    },
    {
        "sha": "a34",
        "parent_shas": [],
        "cherry_pick_sha": None,
    }
]

# 4bf
#  | \
#  | 431
#  | /
# 8bb
#  | \
#  | a6c
#  | /
# 6b6
#  | \
#  | 616
#  | /
# 4c2
#  | \
#  | 79c
#  | /
# 216
#  | \
#  | 97b
#  | /
# 3ac
#  |
# 562
#  |
# 9fb


CHERRY_PICK_DEV_LOG = [
    {
        "sha": "4bf",
        "parent_shas": ["8bb", "431"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "431",
        "parent_shas": ["8bb"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "8bb",
        "parent_shas": ["6b6", "a6c"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "a6c",
        "parent_shas": ["6b6"],
        "cherry_pick_sha": "a19",
    },
    {
        "sha": "6b6",
        "parent_shas": ["4c2", "616"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "616",
        "parent_shas": ["4c2"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "4c2",
        "parent_shas": ["216", "79c"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "79c",
        "parent_shas": ["216"],
        "cherry_pick_sha": "99f",
    },
    {
        "sha": "216",
        "parent_shas": ["3ac", "97b"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "97b",
        "parent_shas": ["3ac"],
        "cherry_pick_sha": "b56",
    },
    {
        "sha": "3ac",
        "parent_shas": ["562"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "562",
        "parent_shas": ["9fb"],
        "cherry_pick_sha": None,
    },
    {
        "sha": "9fb",
        "parent_shas": [],
        "cherry_pick_sha": "a34",
    }
]
