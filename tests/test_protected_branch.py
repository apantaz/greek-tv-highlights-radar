from greek_tv.dev.protected_branch import branch_name, main


def test_extracts_branch_name_from_git_ref():
    assert branch_name("refs/heads/feature/pre-commit") == "feature/pre-commit"
    assert branch_name("main") == "main"
    assert branch_name(None) is None


def test_rejects_push_to_main(monkeypatch, capsys):
    monkeypatch.setenv("PRE_COMMIT_REMOTE_BRANCH", "refs/heads/main")

    assert main() == 1
    assert "Direct pushes to 'main' are blocked" in capsys.readouterr().err


def test_rejects_push_to_master(monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_REMOTE_BRANCH", "refs/heads/master")

    assert main() == 1


def test_allows_push_to_feature_branch(monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_REMOTE_BRANCH", "refs/heads/feature/pre-commit")

    assert main() == 0
