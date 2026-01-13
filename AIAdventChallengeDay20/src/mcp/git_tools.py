"""Git repository tools for MCP."""

from typing import Dict, List, Optional
from pathlib import Path
import git
from datetime import datetime


class GitTools:
    """Git repository information tools."""

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize git tools.

        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = repo_path or Path.cwd()
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            self.repo = None
            print(f"Warning: {self.repo_path} is not a git repository")

    def get_current_branch(self) -> Dict:
        """
        Get current git branch information.

        Returns:
            Dictionary with branch info
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            branch = self.repo.active_branch
            return {
                "name": branch.name,
                "commit": str(branch.commit),
                "commit_message": branch.commit.message.strip(),
                "author": str(branch.commit.author),
                "date": branch.commit.committed_datetime.isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    def get_status(self) -> Dict:
        """
        Get git status information.

        Returns:
            Dictionary with status info
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            status = {
                "branch": self.repo.active_branch.name,
                "modified": [item.a_path for item in self.repo.index.diff(None)],
                "staged": [item.a_path for item in self.repo.index.diff("HEAD")],
                "untracked": self.repo.untracked_files,
                "is_dirty": self.repo.is_dirty()
            }
            return status
        except Exception as e:
            return {"error": str(e)}

    def get_recent_commits(self, limit: int = 5) -> List[Dict]:
        """
        Get recent commits.

        Args:
            limit: Number of commits to retrieve

        Returns:
            List of commit information
        """
        if not self.repo:
            return [{"error": "Not a git repository"}]

        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat(),
                    "files_changed": len(commit.stats.files)
                })
            return commits
        except Exception as e:
            return [{"error": str(e)}]

    def get_file_history(self, file_path: str, limit: int = 5) -> List[Dict]:
        """
        Get commit history for a specific file.

        Args:
            file_path: Path to file
            limit: Number of commits

        Returns:
            List of commits affecting the file
        """
        if not self.repo:
            return [{"error": "Not a git repository"}]

        try:
            commits = []
            for commit in self.repo.iter_commits(paths=file_path, max_count=limit):
                commits.append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat()
                })
            return commits
        except Exception as e:
            return [{"error": str(e)}]

    def get_branches(self) -> List[str]:
        """
        Get all branches.

        Returns:
            List of branch names
        """
        if not self.repo:
            return ["error: Not a git repository"]

        try:
            return [branch.name for branch in self.repo.branches]
        except Exception as e:
            return [f"error: {e}"]

    def get_remote_info(self) -> Dict:
        """
        Get remote repository information.

        Returns:
            Dictionary with remote info
        """
        if not self.repo:
            return {"error": "Not a git repository"}

        try:
            remotes = {}
            for remote in self.repo.remotes:
                remotes[remote.name] = {
                    "url": list(remote.urls)[0] if remote.urls else None,
                    "fetch": remote.exists()
                }
            return remotes
        except Exception as e:
            return {"error": str(e)}

    def get_diff(self, cached: bool = False) -> str:
        """
        Get git diff.

        Args:
            cached: If True, get staged diff

        Returns:
            Diff text
        """
        if not self.repo:
            return "Error: Not a git repository"

        try:
            if cached:
                return self.repo.git.diff('--cached')
            else:
                return self.repo.git.diff()
        except Exception as e:
            return f"Error: {e}"
