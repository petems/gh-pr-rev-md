"""Comprehensive tests for git_utils.py native git parsing functionality."""

import os
import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

from gh_pr_rev_md.git_utils import GitParsingError, GitRepository, RemoteInfo


class TestGitRepository:
    """Test cases for GitRepository class."""

    def test_init_with_valid_git_repo(self, tmp_path):
        """Test GitRepository initialization with a valid git repository."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        repo = GitRepository(str(tmp_path))
        assert repo.git_dir == git_dir
        assert repo.repo_path == tmp_path.resolve()

    def test_init_with_nested_git_repo(self, tmp_path):
        """Test GitRepository finds .git directory in parent directories."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        nested_dir = tmp_path / "src" / "components"
        nested_dir.mkdir(parents=True)
        
        repo = GitRepository(str(nested_dir))
        assert repo.git_dir == git_dir

    def test_init_with_worktree_git_file(self, tmp_path):
        """Test GitRepository handles worktree .git files."""
        main_git_dir = tmp_path / "main_repo" / ".git"
        main_git_dir.mkdir(parents=True)
        
        worktree_git_dir = main_git_dir / "worktrees" / "feature_branch"
        worktree_git_dir.mkdir(parents=True)
        
        worktree_dir = tmp_path / "feature_worktree"
        worktree_dir.mkdir()
        
        # Create .git file pointing to worktree gitdir
        git_file = worktree_dir / ".git"
        git_file.write_text(f"gitdir: {worktree_git_dir}")
        
        repo = GitRepository(str(worktree_dir))
        assert repo.git_dir == worktree_git_dir

    def test_init_with_relative_gitdir_path(self, tmp_path):
        """Test GitRepository handles relative gitdir paths in .git files."""
        main_git_dir = tmp_path / ".git"
        main_git_dir.mkdir()
        
        worktree_git_dir = main_git_dir / "worktrees" / "feature"
        worktree_git_dir.mkdir(parents=True)
        
        worktree_dir = tmp_path / "worktree"
        worktree_dir.mkdir()
        
        # Create .git file with relative path
        git_file = worktree_dir / ".git"
        git_file.write_text("gitdir: ../.git/worktrees/feature")
        
        repo = GitRepository(str(worktree_dir))
        assert repo.git_dir == worktree_git_dir

    def test_init_not_in_git_repo(self, tmp_path):
        """Test GitRepository raises error when not in a git repository."""
        with pytest.raises(GitParsingError, match="Not in a git repository"):
            GitRepository(str(tmp_path))

    def test_init_invalid_git_file(self, tmp_path):
        """Test GitRepository handles invalid .git files gracefully."""
        git_file = tmp_path / ".git"
        git_file.write_text("invalid content")
        
        with pytest.raises(GitParsingError, match="Not in a git repository"):
            GitRepository(str(tmp_path))

    def test_init_unreadable_git_file(self, tmp_path):
        """Test GitRepository handles unreadable .git files."""
        git_file = tmp_path / ".git"
        git_file.write_bytes(b"\xff\xfe\xfd")  # Invalid UTF-8 bytes
        
        with pytest.raises(GitParsingError, match="Failed to read .git file"):
            GitRepository(str(tmp_path))


class TestGetCurrentBranch:
    """Test cases for get_current_branch method."""

    def create_git_repo(self, tmp_path):
        """Helper to create a basic git repository structure."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        return GitRepository(str(tmp_path))

    def test_get_current_branch_symbolic_ref(self, tmp_path):
        """Test getting current branch from symbolic ref."""
        repo = self.create_git_repo(tmp_path)
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("ref: refs/heads/main")
        
        branch = repo.get_current_branch()
        assert branch == "main"

    def test_get_current_branch_feature_branch(self, tmp_path):
        """Test getting current branch for feature branches."""
        repo = self.create_git_repo(tmp_path)
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("ref: refs/heads/feature/user-auth")
        
        branch = repo.get_current_branch()
        assert branch == "feature/user-auth"

    def test_get_current_branch_detached_head(self, tmp_path):
        """Test getting current branch when in detached HEAD state."""
        repo = self.create_git_repo(tmp_path)
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("a1b2c3d4e5f6789012345678901234567890abcd")
        
        branch = repo.get_current_branch()
        assert branch is None

    def test_get_current_branch_tag_ref(self, tmp_path):
        """Test getting current branch when HEAD points to a tag."""
        repo = self.create_git_repo(tmp_path)
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("ref: refs/tags/v1.0.0")
        
        branch = repo.get_current_branch()
        assert branch == "v1.0.0"

    def test_get_current_branch_remote_ref(self, tmp_path):
        """Test getting current branch when HEAD points to a remote ref."""
        repo = self.create_git_repo(tmp_path)
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("ref: refs/remotes/origin/main")
        
        branch = repo.get_current_branch()
        assert branch == "main"

    def test_get_current_branch_missing_head_file(self, tmp_path):
        """Test error handling when HEAD file is missing."""
        repo = self.create_git_repo(tmp_path)
        
        with pytest.raises(GitParsingError, match="Failed to read HEAD file"):
            repo.get_current_branch()

    def test_get_current_branch_unreadable_head_file(self, tmp_path):
        """Test error handling when HEAD file is unreadable."""
        repo = self.create_git_repo(tmp_path)
        head_file = repo.git_dir / "HEAD"
        head_file.write_bytes(b"\xff\xfe\xfd")  # Invalid UTF-8 bytes
        
        with pytest.raises(GitParsingError, match="Failed to read HEAD file"):
            repo.get_current_branch()


class TestGetRemoteUrl:
    """Test cases for get_remote_url method."""

    def create_git_repo_with_config(self, tmp_path, config_content):
        """Helper to create git repo with specific config content."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config_file = git_dir / "config"
        config_file.write_text(config_content)
        return GitRepository(str(tmp_path))

    def test_get_remote_url_origin_default(self, tmp_path):
        """Test getting remote URL for default origin remote."""
        config_content = """
[remote "origin"]
    url = https://github.com/owner/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        url = repo.get_remote_url()
        assert url == "https://github.com/owner/repo.git"

    def test_get_remote_url_specific_remote(self, tmp_path):
        """Test getting remote URL for a specific remote."""
        config_content = """
[remote "upstream"]
    url = https://github.com/upstream/repo.git
    fetch = +refs/heads/*:refs/remotes/upstream/*

[remote "origin"]
    url = https://github.com/fork/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        url = repo.get_remote_url("upstream")
        assert url == "https://github.com/upstream/repo.git"

    def test_get_remote_url_branch_tracking(self, tmp_path):
        """Test getting remote URL based on current branch's tracking remote."""
        config_content = """
[branch "feature"]
    remote = upstream
    merge = refs/heads/feature

[remote "upstream"]
    url = https://github.com/upstream/repo.git
    fetch = +refs/heads/*:refs/remotes/upstream/*

[remote "origin"]
    url = https://github.com/fork/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        # Mock current branch
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("ref: refs/heads/feature")
        
        url = repo.get_remote_url()
        assert url == "https://github.com/upstream/repo.git"

    def test_get_remote_url_fallback_to_origin(self, tmp_path):
        """Test fallback to origin when branch tracking is not configured."""
        config_content = """
[branch "feature"]
    merge = refs/heads/feature

[remote "upstream"]
    url = https://github.com/upstream/repo.git
    fetch = +refs/heads/*:refs/remotes/upstream/*

[remote "origin"]
    url = https://github.com/origin/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        # Mock current branch
        head_file = repo.git_dir / "HEAD"
        head_file.write_text("ref: refs/heads/feature")
        
        url = repo.get_remote_url()
        assert url == "https://github.com/origin/repo.git"

    def test_get_remote_url_first_available_remote(self, tmp_path):
        """Test using first available remote when origin doesn't exist."""
        config_content = """
[remote "upstream"]
    url = https://github.com/upstream/repo.git
    fetch = +refs/heads/*:refs/remotes/upstream/*
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        url = repo.get_remote_url()
        assert url == "https://github.com/upstream/repo.git"

    def test_get_remote_url_ssh_format(self, tmp_path):
        """Test getting SSH format remote URL."""
        config_content = """
[remote "origin"]
    url = git@github.com:owner/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        url = repo.get_remote_url()
        assert url == "git@github.com:owner/repo.git"

    def test_get_remote_url_no_config_file(self, tmp_path):
        """Test handling when config file doesn't exist."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        repo = GitRepository(str(tmp_path))
        
        url = repo.get_remote_url()
        assert url is None

    def test_get_remote_url_no_remotes(self, tmp_path):
        """Test handling when no remotes are configured."""
        config_content = """
[core]
    repositoryformatversion = 0
    filemode = true
"""
        repo = self.create_git_repo_with_config(tmp_path, config_content)
        
        url = repo.get_remote_url()
        assert url is None

    def test_get_remote_url_invalid_config(self, tmp_path):
        """Test error handling with invalid config file."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config_file = git_dir / "config"
        config_file.write_text("invalid config content [[[")
        
        repo = GitRepository(str(tmp_path))
        
        with pytest.raises(GitParsingError, match="Failed to parse git config"):
            repo.get_remote_url()

    def test_get_remote_url_unreadable_config(self, tmp_path):
        """Test error handling when config file is unreadable."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config_file = git_dir / "config"
        config_file.write_bytes(b"\xff\xfe\xfd")  # Invalid UTF-8 bytes
        
        repo = GitRepository(str(tmp_path))
        
        with pytest.raises(GitParsingError, match="Failed to read git config"):
            repo.get_remote_url()


class TestParseRemoteUrl:
    """Test cases for parse_remote_url method."""

    def create_git_repo(self, tmp_path):
        """Helper to create a basic git repository."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        return GitRepository(str(tmp_path))

    def test_parse_remote_url_https_github(self, tmp_path):
        """Test parsing HTTPS GitHub URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("https://github.com/owner/repo.git")
        
        assert remote_info is not None
        assert remote_info.host == "github.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"
        assert remote_info.url == "https://github.com/owner/repo.git"
        assert remote_info.is_github is True

    def test_parse_remote_url_https_github_no_git_suffix(self, tmp_path):
        """Test parsing HTTPS GitHub URL without .git suffix."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("https://github.com/owner/repo")
        
        assert remote_info is not None
        assert remote_info.host == "github.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"

    def test_parse_remote_url_ssh_github(self, tmp_path):
        """Test parsing SSH GitHub URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("git@github.com:owner/repo.git")
        
        assert remote_info is not None
        assert remote_info.host == "github.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"
        assert remote_info.url == "git@github.com:owner/repo.git"
        assert remote_info.is_github is True

    def test_parse_remote_url_ssh_github_no_git_suffix(self, tmp_path):
        """Test parsing SSH GitHub URL without .git suffix."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("git@github.com:owner/repo")
        
        assert remote_info is not None
        assert remote_info.host == "github.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"

    def test_parse_remote_url_github_enterprise(self, tmp_path):
        """Test parsing GitHub Enterprise URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("https://github.enterprise.com/owner/repo.git")
        
        assert remote_info is not None
        assert remote_info.host == "github.enterprise.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"
        assert remote_info.is_github is True

    def test_parse_remote_url_ssh_github_enterprise(self, tmp_path):
        """Test parsing SSH GitHub Enterprise URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("git@github.enterprise.com:owner/repo.git")
        
        assert remote_info is not None
        assert remote_info.host == "github.enterprise.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"
        assert remote_info.is_github is True

    def test_parse_remote_url_non_github(self, tmp_path):
        """Test parsing non-GitHub URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("https://gitlab.com/owner/repo.git")
        
        assert remote_info is not None
        assert remote_info.host == "gitlab.com"
        assert remote_info.owner == "owner"
        assert remote_info.repo == "repo"
        assert remote_info.is_github is False

    def test_parse_remote_url_invalid_format(self, tmp_path):
        """Test parsing invalid URL format."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("invalid-url")
        assert remote_info is None

    def test_parse_remote_url_empty_string(self, tmp_path):
        """Test parsing empty URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url("")
        assert remote_info is None

    def test_parse_remote_url_none(self, tmp_path):
        """Test parsing None URL."""
        repo = self.create_git_repo(tmp_path)
        
        remote_info = repo.parse_remote_url(None)
        assert remote_info is None

    def test_parse_remote_url_complex_repo_names(self, tmp_path):
        """Test parsing URLs with complex repository names."""
        repo = self.create_git_repo(tmp_path)
        
        test_cases = [
            ("https://github.com/owner-name/repo-name.git", "owner-name", "repo-name"),
            ("https://github.com/owner_name/repo_name.git", "owner_name", "repo_name"),
            ("git@github.com:org.name/repo.name.git", "org.name", "repo.name"),
        ]
        
        for url, expected_owner, expected_repo in test_cases:
            remote_info = repo.parse_remote_url(url)
            assert remote_info is not None
            assert remote_info.owner == expected_owner
            assert remote_info.repo == expected_repo


class TestGetRepositoryInfo:
    """Test cases for get_repository_info method."""

    def create_complete_git_repo(self, tmp_path, branch="main", remote_url="https://github.com/owner/repo.git"):
        """Helper to create a complete git repo with branch and remote."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Create HEAD file
        head_file = git_dir / "HEAD"
        head_file.write_text(f"ref: refs/heads/{branch}")
        
        # Create config file
        config_content = f"""
[remote "origin"]
    url = {remote_url}
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        config_file = git_dir / "config"
        config_file.write_text(config_content)
        
        return GitRepository(str(tmp_path))

    def test_get_repository_info_complete(self, tmp_path):
        """Test getting complete repository information."""
        repo = self.create_complete_git_repo(tmp_path)
        
        info = repo.get_repository_info()
        
        assert info is not None
        host, owner, repo_name, branch = info
        assert host == "github.com"
        assert owner == "owner"
        assert repo_name == "repo"
        assert branch == "main"

    def test_get_repository_info_github_enterprise(self, tmp_path):
        """Test getting repository info for GitHub Enterprise."""
        repo = self.create_complete_git_repo(
            tmp_path, 
            branch="feature/auth",
            remote_url="https://github.enterprise.com/company/project.git"
        )
        
        info = repo.get_repository_info()
        
        assert info is not None
        host, owner, repo_name, branch = info
        assert host == "github.enterprise.com"
        assert owner == "company"
        assert repo_name == "project"
        assert branch == "feature/auth"

    def test_get_repository_info_ssh_url(self, tmp_path):
        """Test getting repository info with SSH URL."""
        repo = self.create_complete_git_repo(
            tmp_path,
            remote_url="git@github.com:owner/repo.git"
        )
        
        info = repo.get_repository_info()
        
        assert info is not None
        host, owner, repo_name, branch = info
        assert host == "github.com"
        assert owner == "owner"
        assert repo_name == "repo"
        assert branch == "main"

    def test_get_repository_info_detached_head(self, tmp_path):
        """Test getting repository info in detached HEAD state."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Create HEAD file with commit hash
        head_file = git_dir / "HEAD"
        head_file.write_text("a1b2c3d4e5f6789012345678901234567890abcd")
        
        # Create config file
        config_content = """
[remote "origin"]
    url = https://github.com/owner/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
"""
        config_file = git_dir / "config"
        config_file.write_text(config_content)
        
        repo = GitRepository(str(tmp_path))
        
        info = repo.get_repository_info()
        assert info is None

    def test_get_repository_info_no_remote(self, tmp_path):
        """Test getting repository info when no remote is configured."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Create HEAD file
        head_file = git_dir / "HEAD"
        head_file.write_text("ref: refs/heads/main")
        
        # Create config file without remotes
        config_content = """
[core]
    repositoryformatversion = 0
"""
        config_file = git_dir / "config"
        config_file.write_text(config_content)
        
        repo = GitRepository(str(tmp_path))
        
        info = repo.get_repository_info()
        assert info is None

    def test_get_repository_info_non_github_remote(self, tmp_path):
        """Test getting repository info for non-GitHub remote."""
        repo = self.create_complete_git_repo(
            tmp_path,
            remote_url="https://gitlab.com/owner/repo.git"
        )
        
        info = repo.get_repository_info()
        assert info is None

    def test_get_repository_info_invalid_remote_url(self, tmp_path):
        """Test getting repository info with invalid remote URL."""
        repo = self.create_complete_git_repo(
            tmp_path,
            remote_url="invalid-url"
        )
        
        info = repo.get_repository_info()
        assert info is None

    def test_get_repository_info_parsing_error(self, tmp_path):
        """Test getting repository info when parsing fails."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Create invalid HEAD file
        head_file = git_dir / "HEAD"
        head_file.write_bytes(b"\x00\x01\x02")  # Invalid UTF-8
        
        repo = GitRepository(str(tmp_path))
        
        info = repo.get_repository_info()
        assert info is None


class TestRemoteInfo:
    """Test cases for RemoteInfo dataclass."""

    def test_remote_info_github_detection(self):
        """Test GitHub detection in RemoteInfo."""
        github_remote = RemoteInfo(
            host="github.com",
            owner="owner", 
            repo="repo",
            url="https://github.com/owner/repo.git"
        )
        assert github_remote.is_github is True

    def test_remote_info_github_enterprise_detection(self):
        """Test GitHub Enterprise detection in RemoteInfo."""
        ghe_remote = RemoteInfo(
            host="github.enterprise.com",
            owner="owner",
            repo="repo", 
            url="https://github.enterprise.com/owner/repo.git"
        )
        assert ghe_remote.is_github is True

    def test_remote_info_non_github_detection(self):
        """Test non-GitHub detection in RemoteInfo."""
        gitlab_remote = RemoteInfo(
            host="gitlab.com",
            owner="owner",
            repo="repo",
            url="https://gitlab.com/owner/repo.git"
        )
        assert gitlab_remote.is_github is False