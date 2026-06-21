# tests/test_models.py
from src.models.models import GitHubRepository


def test_parse_ssh_scp_form():
    repo = GitHubRepository.parse("git@github.com:owner/name.git")
    assert repo.owner == "owner"
    assert repo.name == "name"
    assert repo.clone_url == "git@github.com:owner/name.git"
