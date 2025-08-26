"""Native Git repository introspection utilities."""

import os
import re
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


class GitParsingError(Exception):
    """Exception raised when git repository parsing fails."""
    pass


@dataclass
class RemoteInfo:
    """Information about a git remote URL."""
    host: str
    owner: str
    repo: str
    url: str
    
    @property
    def is_github(self) -> bool:
        """Check if this is a GitHub or GitHub Enterprise remote."""
        return 'github' in self.host.lower()


class GitRepository:
    """Native git repository introspection without subprocess calls."""
    
    def __init__(self, path: str = "."):
        """Initialize git repository from given path.
        
        Args:
            path: Starting path to search for git repository
            
        Raises:
            GitParsingError: If no git repository found or invalid repository
        """
        self.repo_path = Path(path).resolve()
        self.git_dir = self._find_git_dir()
        
    def _find_git_dir(self) -> Path:
        """Find the .git directory by walking up the directory tree.
        
        Returns:
            Path to the git directory
            
        Raises:
            GitParsingError: If no git repository found
        """
        current_path = self.repo_path
        
        while current_path != current_path.parent:
            git_path = current_path / ".git"
            
            if git_path.is_dir():
                return git_path
            elif git_path.is_file():
                # Handle worktrees: .git file contains "gitdir: /path/to/gitdir"
                try:
                    content = git_path.read_text(encoding="utf-8", errors="strict").strip()
                    if content.startswith("gitdir: "):
                        gitdir_path = content[8:]  # Remove "gitdir: " prefix
                        if not os.path.isabs(gitdir_path):
                            gitdir_path = current_path / gitdir_path
                        gitdir_path = Path(gitdir_path).resolve()
                        if gitdir_path.is_dir():
                            return gitdir_path
                except (OSError, UnicodeDecodeError) as e:
                    raise GitParsingError(f"Failed to read .git file: {e}") from e
                # If .git file exists but doesn't contain valid gitdir, continue searching
                # This handles cases where .git file is malformed but we can still find
                # a .git directory in parent directories
            
            current_path = current_path.parent
        
        raise GitParsingError("Not in a git repository")
    
    def _get_common_git_dir(self) -> Optional[Path]:
        """Get the common git directory for worktrees.
        
        Returns:
            Path to common git directory if this is a worktree, None otherwise
        """
        commondir_file = self.git_dir / "commondir"
        if commondir_file.exists():
            try:
                commondir_content = commondir_file.read_text(encoding="utf-8", errors="strict").strip()
                if commondir_content:
                    common_path = self.git_dir / commondir_content
                    return common_path.resolve()
            except (OSError, UnicodeDecodeError):
                pass
        return None
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name.
        
        Returns:
            Branch name if on a branch, None if in detached HEAD state
            
        Raises:
            GitParsingError: If HEAD file cannot be read or parsed
        """
        head_file = self.git_dir / "HEAD"
        
        try:
            head_content = head_file.read_text(encoding="utf-8", errors="strict").strip()
        except (OSError, UnicodeDecodeError) as e:
            raise GitParsingError(f"Failed to read HEAD file: {e}") from e
        
        if head_content.startswith("ref: "):
            # Symbolic ref: "ref: refs/heads/branch-name"
            ref_path = head_content[5:]  # Remove "ref: " prefix
            if ref_path.startswith("refs/heads/"):
                return ref_path[11:]  # Remove "refs/heads/" prefix
            else:
                # Handle other ref types (tags, remotes, etc.)
                return ref_path.split("/")[-1]
        else:
            # Detached HEAD: direct commit hash
            return None
    
    def get_remote_url(self, remote_name: Optional[str] = None) -> Optional[str]:
        """Get remote URL for the specified remote or current branch's remote.
        
        Args:
            remote_name: Specific remote to get URL for. If None, tries to find
                        the appropriate remote for current branch.
        
        Returns:
            Remote URL if found, None otherwise
            
        Raises:
            GitParsingError: If config file cannot be read
        """
        config_file = self.git_dir / "config"
        
        if not config_file.exists():
            return None
            
        try:
            config_content = config_file.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as e:
            raise GitParsingError(f"Failed to read git config: {e}") from e
        
        config = self._parse_git_config(config_content)
        
        # If no specific remote requested, try to find the best one
        if remote_name is None:
            try:
                current_branch = self.get_current_branch()
                if current_branch:
                    # Check if current branch has a configured remote
                    branch_section = f"branch {current_branch}"
                    if config.has_section(branch_section) and config.has_option(branch_section, "remote"):
                        remote_name = config.get(branch_section, "remote")
            except GitParsingError:
                # If we can't read current branch, that's okay - we'll fall back to default remotes
                pass
            
            # Fall back to 'origin' if no branch-specific remote
            if remote_name is None:
                remote_name = "origin"
        
        # Get URL for the remote
        remote_section = f"remote {remote_name}"
        if config.has_section(remote_section) and config.has_option(remote_section, "url"):
            return config.get(remote_section, "url")
        
        # If specified remote not found and it wasn't 'origin', try 'origin'
        if remote_name != "origin":
            origin_section = "remote origin"
            if config.has_section(origin_section) and config.has_option(origin_section, "url"):
                return config.get(origin_section, "url")
        
        # Last resort: return first remote found
        for section_name in config.sections():
            if section_name.startswith("remote ") and config.has_option(section_name, "url"):
                return config.get(section_name, "url")
        
        return None
    
    def _parse_git_config(self, config_content: str) -> ConfigParser:
        """Parse git config content, handling git-specific section format.
        
        Git uses section format like [remote "origin"] which needs to be
        converted to ConfigParser format [remote origin].
        
        Args:
            config_content: Raw git config file content
            
        Returns:
            Parsed ConfigParser object
            
        Raises:
            GitParsingError: If config cannot be parsed
        """
        config = ConfigParser()
        
        try:
            # Convert git config format to ConfigParser format
            normalized_content = self._normalize_git_config_format(config_content)
            config.read_string(normalized_content)
        except Exception as e:
            raise GitParsingError(f"Failed to parse git config: {e}") from e
            
        return config
    
    def _normalize_git_config_format(self, config_content: str) -> str:
        """Convert git config section format to ConfigParser format.

        Converts [remote "origin"] to [remote origin] so ConfigParser can handle it.

        Args:
            config_content: Raw git config content

        Returns:
            Normalized config content for ConfigParser
        """
        # Regex to find sections like [type "name"] and replace them
        section_pattern = re.compile(r'\[\s*([^\[\]\s"]+)\s*"([^"]+)"\s*\]')
        return section_pattern.sub(r'[\1 \2]', config_content)
    
    def parse_remote_url(self, remote_url: str) -> Optional[RemoteInfo]:
        """Parse a git remote URL to extract repository information.
        
        Args:
            remote_url: Git remote URL (SSH or HTTPS format)
            
        Returns:
            RemoteInfo object if URL is parseable, None otherwise
        """
        if not remote_url:
            return None
        
        # Handle SSH format: git@github.com:owner/repo.git
        ssh_pattern = r"^git@([^:]+):([^/]+)/([^/]+?)(?:\.git)?$"
        ssh_match = re.match(ssh_pattern, remote_url)
        if ssh_match:
            host, owner, repo = ssh_match.groups()
            return RemoteInfo(host=host, owner=owner, repo=repo, url=remote_url)
        
        # Handle HTTPS format: https://github.com/owner/repo.git
        https_pattern = r"^https://([^/]+)/([^/]+)/([^/]+?)(?:\.git)?$"
        https_match = re.match(https_pattern, remote_url)
        if https_match:
            host, owner, repo = https_match.groups()
            return RemoteInfo(host=host, owner=owner, repo=repo, url=remote_url)
        
        return None
    
    def get_repository_info(self) -> Optional[Tuple[str, str, str, str]]:
        """Get complete repository information for GitHub PR URL construction.
        
        Returns:
            Tuple of (host, owner, repo, branch) if all information available,
            None if any required information is missing
        """
        try:
            branch = self.get_current_branch()
            if branch is None:
                return None  # Detached HEAD
            
            remote_url = self.get_remote_url()
            if remote_url is None:
                return None  # No remote configured
            
            remote_info = self.parse_remote_url(remote_url)
            if remote_info is None or not remote_info.is_github:
                return None  # Not a GitHub repository
            
            return remote_info.host, remote_info.owner, remote_info.repo, branch
            
        except GitParsingError:
            return None
    
    def get_current_commit_hash(self) -> Optional[str]:
        """Get the current commit hash.
        
        Returns:
            Short commit hash (7 characters) if available, None otherwise
            
        Raises:
            GitParsingError: If HEAD file cannot be read or parsed
        """
        head_file = self.git_dir / "HEAD"
        
        try:
            head_content = head_file.read_text(encoding="utf-8", errors="strict").strip()
        except (OSError, UnicodeDecodeError) as e:
            raise GitParsingError(f"Failed to read HEAD file: {e}") from e
        
        if head_content.startswith("ref: "):
            # Symbolic ref: need to resolve to actual commit hash
            ref_path = head_content[5:]  # Remove "ref: " prefix
            ref_file = self.git_dir / ref_path
            
            # For worktrees, refs might be in the common git directory
            if not ref_file.exists():
                common_git_dir = self._get_common_git_dir()
                if common_git_dir:
                    ref_file = common_git_dir / ref_path
            
            try:
                if ref_file.exists():
                    commit_hash = ref_file.read_text(encoding="utf-8", errors="strict").strip()
                    return commit_hash[:7] if len(commit_hash) >= 7 else commit_hash
            except (OSError, UnicodeDecodeError) as e:
                raise GitParsingError(f"Failed to read ref file {ref_file}: {e}") from e
        else:
            # Direct commit hash
            return head_content[:7] if len(head_content) >= 7 else head_content
        
        return None
    
    def get_current_tag(self) -> Optional[str]:
        """Get the current git tag if HEAD is pointing to a tagged commit.
        
        Returns:
            Tag name if current commit has a tag, None otherwise
            
        Raises:
            GitParsingError: If unable to read git refs or HEAD
        """
        try:
            # Get the full commit hash for comparison
            head_file = self.git_dir / "HEAD"
            head_content = head_file.read_text(encoding="utf-8", errors="strict").strip()
            
            if head_content.startswith("ref: "):
                ref_path = head_content[5:]
                ref_file = self.git_dir / ref_path
                
                # For worktrees, refs might be in the common git directory
                if not ref_file.exists():
                    common_git_dir = self._get_common_git_dir()
                    if common_git_dir:
                        ref_file = common_git_dir / ref_path
                
                if ref_file.exists():
                    full_commit = ref_file.read_text(encoding="utf-8", errors="strict").strip()
                else:
                    return None
            else:
                full_commit = head_content
                
        except (OSError, UnicodeDecodeError) as e:
            raise GitParsingError(f"Failed to get current commit: {e}") from e
        
        # Check all tags to see if any point to the current commit
        # First try the worktree's tags directory
        tags_dir = self.git_dir / "refs" / "tags"
        
        # If tags don't exist in worktree, try common git directory
        if not tags_dir.exists():
            common_git_dir = self._get_common_git_dir()
            if common_git_dir:
                tags_dir = common_git_dir / "refs" / "tags"
        
        if not tags_dir.exists():
            return None
        
        try:
            for tag_file in tags_dir.rglob("*"):
                if tag_file.is_file():
                    try:
                        tag_commit = tag_file.read_text(encoding="utf-8", errors="strict").strip()
                        if tag_commit == full_commit:
                            # Get tag name (relative to tags directory)
                            tag_name = str(tag_file.relative_to(tags_dir))
                            return tag_name
                    except (OSError, UnicodeDecodeError):
                        # Skip this tag if we can't read it
                        continue
        except (OSError,) as e:
            raise GitParsingError(f"Failed to read tags directory: {e}") from e
        
        return None
    
    def get_version_info(self) -> str:
        """Get version information combining tag, commit, and branch data.
        
        Returns:
            Formatted version string:
            - "v1.2.3" if on a tagged commit
            - "abc123f (branch-name)" if on untagged commit with branch
            - "abc123f" if on untagged commit without branch (detached HEAD)
            - "unknown" if unable to determine any version info
        """
        try:
            # Try to get tag first (highest priority)
            tag = self.get_current_tag()
            if tag:
                return tag
            
            # Get commit hash and branch info
            commit_hash = self.get_current_commit_hash()
            branch = self.get_current_branch()
            
            if commit_hash:
                if branch:
                    return f"{commit_hash} ({branch})"
                else:
                    return commit_hash
            
            # Fallback if we can't determine anything
            return "unknown"
            
        except GitParsingError:
            return "unknown"