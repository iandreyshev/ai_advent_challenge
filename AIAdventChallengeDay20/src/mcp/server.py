"""MCP Server implementation."""

from typing import Dict, Any, List, Callable
from pathlib import Path
import json
from .git_tools import GitTools


class MCPServer:
    """
    MCP Server for providing tools to AI assistant.

    This is a simplified MCP implementation that provides tools
    for git integration and project context.
    """

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize MCP server.

        Args:
            repo_path: Path to git repository
        """
        self.git_tools = GitTools(repo_path)
        self.tools: Dict[str, Callable] = {
            'get_current_branch': self.git_tools.get_current_branch,
            'get_git_status': self.git_tools.get_status,
            'get_recent_commits': self.git_tools.get_recent_commits,
            'get_file_history': self.git_tools.get_file_history,
            'get_branches': self.git_tools.get_branches,
            'get_remote_info': self.git_tools.get_remote_info,
            'get_diff': self.git_tools.get_diff,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools.

        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": "get_current_branch",
                "description": "Get information about the current git branch",
                "parameters": {}
            },
            {
                "name": "get_git_status",
                "description": "Get git status (modified, staged, untracked files)",
                "parameters": {}
            },
            {
                "name": "get_recent_commits",
                "description": "Get recent commit history",
                "parameters": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of commits to retrieve",
                        "default": 5
                    }
                }
            },
            {
                "name": "get_file_history",
                "description": "Get commit history for a specific file",
                "parameters": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of commits",
                        "default": 5
                    }
                }
            },
            {
                "name": "get_branches",
                "description": "Get list of all branches",
                "parameters": {}
            },
            {
                "name": "get_remote_info",
                "description": "Get remote repository information",
                "parameters": {}
            },
            {
                "name": "get_diff",
                "description": "Get git diff",
                "parameters": {
                    "cached": {
                        "type": "boolean",
                        "description": "If true, get staged diff",
                        "default": False
                    }
                }
            }
        ]

    def call_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Any:
        """
        Call a tool by name.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            tool = self.tools[tool_name]
            if parameters:
                return tool(**parameters)
            else:
                return tool()
        except Exception as e:
            return {"error": str(e)}

    def get_context(self) -> Dict[str, Any]:
        """
        Get full context for AI assistant.

        Returns:
            Dictionary with git context
        """
        return {
            "branch": self.git_tools.get_current_branch(),
            "status": self.git_tools.get_status(),
            "recent_commits": self.git_tools.get_recent_commits(limit=3),
            "remotes": self.git_tools.get_remote_info()
        }

    def to_json(self) -> str:
        """
        Export server configuration as JSON.

        Returns:
            JSON string
        """
        return json.dumps({
            "name": "git-repo-mcp",
            "version": "1.0.0",
            "tools": self.list_tools()
        }, indent=2)


# Fix import
from typing import Optional
