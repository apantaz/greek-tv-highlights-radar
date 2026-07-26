"""Reject direct pushes to protected branches."""

import os
import subprocess
import sys

PROTECTED_BRANCHES = frozenset({"main", "master"})


def branch_name(ref: str | None) -> str | None:
    if not ref:
        return None
    return ref.removeprefix("refs/heads/")


def current_branch() -> str | None:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or None


def main() -> int:
    remote_branch = branch_name(os.getenv("PRE_COMMIT_REMOTE_BRANCH"))
    branch = remote_branch or current_branch()
    if branch not in PROTECTED_BRANCHES:
        return 0

    print(
        f"Direct pushes to '{branch}' are blocked. "
        "Push a feature branch and open a pull request instead.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
