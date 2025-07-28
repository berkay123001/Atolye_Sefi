"""
🔗 GIT OPERATIONS - Professional Git Integration for GraphAgent
Smart git automation with workspace awareness
"""

import os
import sys
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from pydantic.v1 import BaseModel, Field
from langchain.tools import tool
from datetime import datetime

try:
    import git
    from git import Repo, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("⚠️ GitPython not installed. Run: pip install GitPython")

class GitOperationInput(BaseModel):
    operation: str = Field(description="Git operation: status, add, commit, branch, push, pull, diff")
    message: str = Field(description="Commit message or branch name", default="")
    files: List[str] = Field(description="Files to add (empty for all)", default=[])
    branch: str = Field(description="Branch name for branch operations", default="")

class WorkspaceAwareGitOperations:
    """
    Professional Git operations with workspace awareness and smart automation
    """
    
    def __init__(self, workspace_root: str = None):
        """
        Initialize workspace-aware Git operations
        
        Args:
            workspace_root: Workspace root directory
        """
        self.workspace_root = workspace_root or os.path.join(os.getcwd(), "workspace")
        self.project_root = self._find_git_root()
        self.repo = None
        
        if GIT_AVAILABLE and self.project_root:
            try:
                self.repo = Repo(self.project_root)
                print(f"🔗 Git repository initialized: {self.project_root}")
            except InvalidGitRepositoryError:
                print("⚠️ Not a git repository")
    
    def _find_git_root(self) -> Optional[str]:
        """Find git repository root"""
        current = os.getcwd()
        path = Path(current)
        
        for parent in [path] + list(path.parents):
            if (parent / '.git').exists():
                return str(parent)
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive git status"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            # Get basic status
            status = {
                "status": "success",
                "current_branch": self.repo.active_branch.name,
                "is_dirty": self.repo.is_dirty(),
                "untracked_files": self.repo.untracked_files,
                "modified_files": [item.a_path for item in self.repo.index.diff(None)],
                "staged_files": [item.a_path for item in self.repo.index.diff("HEAD")],
                "total_commits": len(list(self.repo.iter_commits())),
                "last_commit": {
                    "hash": self.repo.head.commit.hexsha[:8],
                    "message": self.repo.head.commit.message.strip(),
                    "author": str(self.repo.head.commit.author),
                    "date": self.repo.head.commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
                }
            }
            
            # Workspace-specific analysis
            workspace_files = self._get_workspace_git_status()
            status["workspace_analysis"] = workspace_files
            
            return status
            
        except Exception as e:
            return {"status": "error", "message": f"Git status error: {str(e)}"}
    
    def _get_workspace_git_status(self) -> Dict[str, Any]:
        """Analyze workspace-specific git status"""
        workspace_status = {
            "workspace_files_modified": [],
            "workspace_files_untracked": [],
            "workspace_files_staged": []
        }
        
        if not self.repo:
            return workspace_status
        
        try:
            # Check workspace files specifically
            for file_path in self.repo.untracked_files:
                if file_path.startswith("workspace/"):
                    workspace_status["workspace_files_untracked"].append(file_path)
            
            for item in self.repo.index.diff(None):
                if item.a_path.startswith("workspace/"):
                    workspace_status["workspace_files_modified"].append(item.a_path)
            
            for item in self.repo.index.diff("HEAD"):
                if item.a_path.startswith("workspace/"):
                    workspace_status["workspace_files_staged"].append(item.a_path)
                    
        except Exception as e:
            print(f"⚠️ Workspace git analysis error: {e}")
        
        return workspace_status
    
    def add_files(self, files: List[str] = None) -> Dict[str, Any]:
        """Add files to git staging"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            if not files:
                # Add all files
                self.repo.git.add('.')
                added_files = "all files"
            else:
                # Add specific files
                for file in files:
                    if os.path.exists(file):
                        self.repo.git.add(file)
                    else:
                        print(f"⚠️ File not found: {file}")
                added_files = ", ".join(files)
            
            return {
                "status": "success",
                "message": f"Added {added_files} to staging",
                "staged_files": [item.a_path for item in self.repo.index.diff("HEAD")]
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Git add error: {str(e)}"}
    
    def commit_changes(self, message: str = None) -> Dict[str, Any]:
        """Commit staged changes with smart message generation"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            # Check if there are staged changes
            staged_files = [item.a_path for item in self.repo.index.diff("HEAD")]
            if not staged_files:
                return {"status": "warning", "message": "No staged changes to commit"}
            
            # Generate smart commit message if not provided
            if not message:
                message = self._generate_smart_commit_message(staged_files)
            
            # Commit changes
            commit = self.repo.index.commit(message)
            
            return {
                "status": "success",
                "message": f"Committed {len(staged_files)} files",
                "commit_hash": commit.hexsha[:8],
                "commit_message": message,
                "files_committed": staged_files
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Git commit error: {str(e)}"}
    
    def _generate_smart_commit_message(self, staged_files: List[str]) -> str:
        """Generate intelligent commit message based on changes"""
        try:
            workspace_files = [f for f in staged_files if f.startswith("workspace/")]
            tool_files = [f for f in staged_files if f.startswith("tools/")]
            agent_files = [f for f in staged_files if f.startswith("agents/")]
            
            # Analyze change types
            if workspace_files:
                if any(".py" in f for f in workspace_files):
                    return "🧪 Update workspace Python files\n\n🤖 Generated with Claude Code"
                else:
                    return "📝 Update workspace documentation\n\n🤖 Generated with Claude Code"
            
            elif tool_files:
                if len(tool_files) == 1:
                    tool_name = Path(tool_files[0]).stem
                    return f"🔧 Enhance {tool_name} functionality\n\n🤖 Generated with Claude Code"
                else:
                    return f"🔧 Update {len(tool_files)} tools\n\n🤖 Generated with Claude Code"
            
            elif agent_files:
                return "🧠 Improve agent capabilities\n\n🤖 Generated with Claude Code"
            
            else:
                return f"✨ Update {len(staged_files)} files\n\n🤖 Generated with Claude Code"
                
        except Exception as e:
            return f"Update project files\n\n🤖 Generated with Claude Code"
    
    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create and switch to new branch"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            # Create new branch
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            
            return {
                "status": "success",
                "message": f"Created and switched to branch '{branch_name}'",
                "current_branch": branch_name,
                "previous_branch": self.repo.heads[0].name
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Branch creation error: {str(e)}"}
    
    def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """Switch to existing branch"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            # Check if branch exists
            if branch_name not in [head.name for head in self.repo.heads]:
                return {"status": "error", "message": f"Branch '{branch_name}' does not exist"}
            
            # Switch branch
            self.repo.heads[branch_name].checkout()
            
            return {
                "status": "success",
                "message": f"Switched to branch '{branch_name}'",
                "current_branch": branch_name
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Branch switch error: {str(e)}"}
    
    def get_diff(self, file_path: str = None) -> Dict[str, Any]:
        """Get git diff for staged or specific files"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            if file_path:
                # Diff for specific file
                if file_path in [item.a_path for item in self.repo.index.diff(None)]:
                    diff = self.repo.git.diff(file_path)
                else:
                    diff = "No changes in file"
            else:
                # Diff for all staged files
                diff = self.repo.git.diff('--cached')
                if not diff:
                    diff = self.repo.git.diff()  # Unstaged changes
            
            return {
                "status": "success",
                "diff": diff,
                "file": file_path or "all files"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Git diff error: {str(e)}"}
    
    def push_changes(self, remote: str = "origin", branch: str = None) -> Dict[str, Any]:
        """Push changes to remote repository"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            current_branch = branch or self.repo.active_branch.name
            
            # Push to remote
            origin = self.repo.remote(remote)
            push_info = origin.push(current_branch)
            
            return {
                "status": "success",
                "message": f"Pushed {current_branch} to {remote}",
                "push_info": str(push_info[0]) if push_info else "Push completed"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Git push error: {str(e)}"}
    
    def pull_changes(self, remote: str = "origin", branch: str = None) -> Dict[str, Any]:
        """Pull changes from remote repository"""
        if not self.repo:
            return {"status": "error", "message": "No git repository found"}
        
        try:
            current_branch = branch or self.repo.active_branch.name
            
            # Pull from remote
            origin = self.repo.remote(remote)
            pull_info = origin.pull(current_branch)
            
            return {
                "status": "success",
                "message": f"Pulled {current_branch} from {remote}",
                "pull_info": str(pull_info[0]) if pull_info else "Pull completed"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Git pull error: {str(e)}"}

# Global workspace-aware Git instance
workspace_git = WorkspaceAwareGitOperations()

@tool(args_schema=GitOperationInput)
def git_operations(operation: str, message: str = "", files: List[str] = [], branch: str = "") -> Dict[str, Any]:
    """
    Professional Git operations with workspace awareness.
    Supports: status, add, commit, branch, push, pull, diff
    """
    print(f"\n🔗 [Git Operations] Executing: {operation}")
    
    if not GIT_AVAILABLE:
        return {
            "status": "error",
            "message": "GitPython not available. Install with: pip install GitPython"
        }
    
    # Route to appropriate operation
    if operation == "status":
        result = workspace_git.get_status()
    elif operation == "add":
        result = workspace_git.add_files(files if files else None)
    elif operation == "commit":
        result = workspace_git.commit_changes(message)
    elif operation == "branch":
        if branch:
            result = workspace_git.create_branch(branch)
        else:
            result = {"status": "error", "message": "Branch name required"}
    elif operation == "switch":
        if branch:
            result = workspace_git.switch_branch(branch)
        else:
            result = {"status": "error", "message": "Branch name required"}
    elif operation == "diff":
        result = workspace_git.get_diff(files[0] if files else None)
    elif operation == "push":
        result = workspace_git.push_changes(branch=branch)
    elif operation == "pull":
        result = workspace_git.pull_changes(branch=branch)
    else:
        result = {
            "status": "error",
            "message": f"Unknown operation: {operation}. Supported: status, add, commit, branch, switch, diff, push, pull"
        }
    
    print(f"✅ Git operation '{operation}' completed: {result.get('status', 'unknown')}")
    
    return result

@tool
def git_smart_commit() -> Dict[str, Any]:
    """
    Smart git workflow: add all workspace changes and commit with AI-generated message
    """
    print("\n🤖 [Smart Git Commit] Starting intelligent workflow...")
    
    if not GIT_AVAILABLE:
        return {
            "status": "error",
            "message": "GitPython not available. Install with: pip install GitPython"
        }
    
    try:
        # Step 1: Check status
        status_result = workspace_git.get_status()
        if status_result["status"] != "success":
            return status_result
        
        # Step 2: Add workspace files if any changes
        workspace_analysis = status_result.get("workspace_analysis", {})
        has_workspace_changes = (
            workspace_analysis.get("workspace_files_modified", []) or
            workspace_analysis.get("workspace_files_untracked", [])
        )
        
        if has_workspace_changes:
            add_result = workspace_git.add_files(["workspace/"])
            if add_result["status"] != "success":
                return add_result
        
        # Step 3: Add all other changes
        add_all_result = workspace_git.add_files()
        if add_all_result["status"] != "success":
            return add_all_result
        
        # Step 4: Smart commit
        commit_result = workspace_git.commit_changes()
        
        return {
            "status": "success",
            "message": "Smart commit workflow completed",
            "workflow_steps": {
                "status_check": "✅",
                "files_added": "✅", 
                "commit_created": "✅"
            },
            "commit_details": commit_result
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Smart commit workflow error: {str(e)}"}