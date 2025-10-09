"""
Enterprise-level Git Manager for Python
Comprehensive Git operations wrapper with enterprise features
"""

import subprocess
import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import re


class GitManager:
    """
    Enterprise-level Git management class providing 100+ Git operations
    with robust error handling, logging, and validation.
    """

    def __init__(self, repo_path: str = ".", log_level: int = logging.INFO):
        """
        Initialize GitManager instance.
        
        Args:
            repo_path: Path to the Git repository (default: current directory)
            log_level: Logging level (default: INFO)
        """
        self.repo_path = Path(repo_path).resolve()
        self._setup_logging(log_level)
        self._validate_git_installation()
        self._validate_repository()

    def _setup_logging(self, log_level: int) -> None:
        """Configure logging for the GitManager."""
        self.logger = logging.getLogger(f"GitManager-{id(self)}")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _validate_git_installation(self) -> None:
        """Validate that Git is installed and accessible."""
        try:
            self._run_command(["git", "--version"])
        except Exception as e:
            raise EnvironmentError(f"Git is not installed or not accessible: {e}")

    def _validate_repository(self) -> None:
        """Validate that the specified path is a Git repository."""
        if not (self.repo_path / ".git").exists():
            self.logger.warning(f"Not a Git repository: {self.repo_path}")

    def _run_command(self, cmd: List[str], check: bool = True, 
                     input_data: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Execute a Git command and return output.
        
        Args:
            cmd: Command as list of strings
            check: Raise exception on non-zero exit code
            input_data: Optional input data for the command
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            self.logger.debug(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                input=input_data,
                check=check
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(cmd)}\n{e.stderr}")
            if check:
                raise
            return e.stdout, e.stderr, e.returncode
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    # ==================== REPOSITORY INITIALIZATION ====================

    def init(self, bare: bool = False, initial_branch: Optional[str] = None) -> bool:
        """
        Initialize a new Git repository.
        
        Args:
            bare: Create a bare repository
            initial_branch: Name of the initial branch
            
        Returns:
            True if successful
        """
        cmd = ["git", "init"]
        if bare:
            cmd.append("--bare")
        if initial_branch:
            cmd.extend(["--initial-branch", initial_branch])
        
        self._run_command(cmd)
        self.logger.info(f"Initialized repository at {self.repo_path}")
        return True

    def clone(self, url: str, target_dir: Optional[str] = None, 
              depth: Optional[int] = None, branch: Optional[str] = None) -> bool:
        """
        Clone a repository.
        
        Args:
            url: Repository URL to clone
            target_dir: Target directory for clone
            depth: Create a shallow clone with history truncated
            branch: Clone specific branch
            
        Returns:
            True if successful
        """
        cmd = ["git", "clone", url]
        if depth:
            cmd.extend(["--depth", str(depth)])
        if branch:
            cmd.extend(["--branch", branch])
        if target_dir:
            cmd.append(target_dir)
        
        self._run_command(cmd)
        self.logger.info(f"Cloned repository from {url}")
        return True

    # ==================== CONFIGURATION ====================

    def config_set(self, key: str, value: str, global_config: bool = False) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            global_config: Set globally instead of locally
            
        Returns:
            True if successful
        """
        cmd = ["git", "config"]
        if global_config:
            cmd.append("--global")
        cmd.extend([key, value])
        
        self._run_command(cmd)
        self.logger.info(f"Set config {key} = {value}")
        return True

    def config_get(self, key: str, global_config: bool = False) -> Optional[str]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            global_config: Get from global config
            
        Returns:
            Configuration value or None
        """
        cmd = ["git", "config"]
        if global_config:
            cmd.append("--global")
        cmd.extend(["--get", key])
        
        stdout, _, code = self._run_command(cmd, check=False)
        return stdout if code == 0 else None

    def config_list(self, global_config: bool = False) -> Dict[str, str]:
        """
        List all configuration values.
        
        Args:
            global_config: List global config
            
        Returns:
            Dictionary of configuration key-value pairs
        """
        cmd = ["git", "config", "--list"]
        if global_config:
            cmd.append("--global")
        
        stdout, _, _ = self._run_command(cmd)
        config = {}
        for line in stdout.split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                config[key] = value
        return config

    def config_unset(self, key: str, global_config: bool = False) -> bool:
        """
        Unset a configuration value.
        
        Args:
            key: Configuration key to unset
            global_config: Unset from global config
            
        Returns:
            True if successful
        """
        cmd = ["git", "config"]
        if global_config:
            cmd.append("--global")
        cmd.extend(["--unset", key])
        
        self._run_command(cmd, check=False)
        self.logger.info(f"Unset config {key}")
        return True

    # ==================== FILE OPERATIONS ====================

    def add(self, files: Union[str, List[str]], force: bool = False) -> bool:
        """
        Add files to staging area.
        
        Args:
            files: File path(s) to add
            force: Force add ignored files
            
        Returns:
            True if successful
        """
        if isinstance(files, str):
            files = [files]
        
        cmd = ["git", "add"]
        if force:
            cmd.append("--force")
        cmd.extend(files)
        
        self._run_command(cmd)
        self.logger.info(f"Added files: {files}")
        return True

    def add_all(self) -> bool:
        """
        Add all changes to staging area.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "add", "-A"])
        self.logger.info("Added all changes")
        return True

    def rm(self, files: Union[str, List[str]], force: bool = False, 
           cached: bool = False) -> bool:
        """
        Remove files from working tree and index.
        
        Args:
            files: File path(s) to remove
            force: Force removal
            cached: Only remove from index
            
        Returns:
            True if successful
        """
        if isinstance(files, str):
            files = [files]
        
        cmd = ["git", "rm"]
        if force:
            cmd.append("--force")
        if cached:
            cmd.append("--cached")
        cmd.extend(files)
        
        self._run_command(cmd)
        self.logger.info(f"Removed files: {files}")
        return True

    def mv(self, source: str, destination: str, force: bool = False) -> bool:
        """
        Move or rename a file.
        
        Args:
            source: Source path
            destination: Destination path
            force: Force move/rename
            
        Returns:
            True if successful
        """
        cmd = ["git", "mv"]
        if force:
            cmd.append("--force")
        cmd.extend([source, destination])
        
        self._run_command(cmd)
        self.logger.info(f"Moved {source} to {destination}")
        return True

    def restore(self, files: Union[str, List[str]], staged: bool = False) -> bool:
        """
        Restore working tree files.
        
        Args:
            files: File path(s) to restore
            staged: Restore staged files
            
        Returns:
            True if successful
        """
        if isinstance(files, str):
            files = [files]
        
        cmd = ["git", "restore"]
        if staged:
            cmd.append("--staged")
        cmd.extend(files)
        
        self._run_command(cmd)
        self.logger.info(f"Restored files: {files}")
        return True

    # ==================== COMMIT OPERATIONS ====================

    def commit(self, message: str, amend: bool = False, 
               all_changes: bool = False, allow_empty: bool = False) -> str:
        """
        Create a commit.
        
        Args:
            message: Commit message
            amend: Amend previous commit
            all_changes: Automatically stage modified and deleted files
            allow_empty: Allow empty commit
            
        Returns:
            Commit hash
        """
        cmd = ["git", "commit", "-m", message]
        if amend:
            cmd.append("--amend")
        if all_changes:
            cmd.append("-a")
        if allow_empty:
            cmd.append("--allow-empty")
        
        stdout, _, _ = self._run_command(cmd)
        commit_hash = self.get_current_commit()
        self.logger.info(f"Created commit: {commit_hash}")
        return commit_hash

    def commit_with_files(self, message: str, files: List[str]) -> str:
        """
        Add specific files and commit.
        
        Args:
            message: Commit message
            files: List of files to commit
            
        Returns:
            Commit hash
        """
        self.add(files)
        return self.commit(message)

    def amend_commit(self, message: Optional[str] = None) -> str:
        """
        Amend the last commit.
        
        Args:
            message: New commit message (None to keep existing)
            
        Returns:
            Commit hash
        """
        cmd = ["git", "commit", "--amend"]
        if message:
            cmd.extend(["-m", message])
        else:
            cmd.append("--no-edit")
        
        self._run_command(cmd)
        commit_hash = self.get_current_commit()
        self.logger.info(f"Amended commit: {commit_hash}")
        return commit_hash

    # ==================== STATUS AND INSPECTION ====================

    def status(self, short: bool = False) -> str:
        """
        Get repository status.
        
        Args:
            short: Use short format
            
        Returns:
            Status output
        """
        cmd = ["git", "status"]
        if short:
            cmd.append("--short")
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    def status_porcelain(self) -> List[Dict[str, str]]:
        """
        Get status in machine-readable format.
        
        Returns:
            List of status entries with index and worktree status
        """
        stdout, _, _ = self._run_command(["git", "status", "--porcelain"])
        statuses = []
        for line in stdout.split("\n"):
            if line:
                statuses.append({
                    "index": line[0],
                    "worktree": line[1],
                    "file": line[3:].strip()
                })
        return statuses

    def diff(self, commit1: Optional[str] = None, commit2: Optional[str] = None,
             files: Optional[List[str]] = None, staged: bool = False) -> str:
        """
        Show changes between commits, working tree, etc.
        
        Args:
            commit1: First commit to compare
            commit2: Second commit to compare
            files: Specific files to diff
            staged: Show staged changes
            
        Returns:
            Diff output
        """
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if commit1:
            cmd.append(commit1)
        if commit2:
            cmd.append(commit2)
        if files:
            cmd.append("--")
            cmd.extend(files)
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    def diff_stat(self, commit1: Optional[str] = None, 
                  commit2: Optional[str] = None) -> str:
        """
        Show diff statistics.
        
        Args:
            commit1: First commit
            commit2: Second commit
            
        Returns:
            Diff statistics
        """
        cmd = ["git", "diff", "--stat"]
        if commit1:
            cmd.append(commit1)
        if commit2:
            cmd.append(commit2)
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    def show(self, ref: str = "HEAD") -> str:
        """
        Show various types of objects.
        
        Args:
            ref: Reference to show (default: HEAD)
            
        Returns:
            Object information
        """
        stdout, _, _ = self._run_command(["git", "show", ref])
        return stdout

    # ==================== BRANCH OPERATIONS ====================

    def branch_list(self, remote: bool = False, all_branches: bool = False) -> List[str]:
        """
        List branches.
        
        Args:
            remote: List remote branches
            all_branches: List all branches
            
        Returns:
            List of branch names
        """
        cmd = ["git", "branch"]
        if remote:
            cmd.append("-r")
        elif all_branches:
            cmd.append("-a")
        
        stdout, _, _ = self._run_command(cmd)
        branches = []
        for line in stdout.split("\n"):
            if line:
                branch = line.strip().lstrip("* ")
                branches.append(branch)
        return branches

    def branch_create(self, name: str, start_point: Optional[str] = None) -> bool:
        """
        Create a new branch.
        
        Args:
            name: Branch name
            start_point: Starting point for new branch
            
        Returns:
            True if successful
        """
        cmd = ["git", "branch", name]
        if start_point:
            cmd.append(start_point)
        
        self._run_command(cmd)
        self.logger.info(f"Created branch: {name}")
        return True

    def branch_delete(self, name: str, force: bool = False) -> bool:
        """
        Delete a branch.
        
        Args:
            name: Branch name
            force: Force deletion
            
        Returns:
            True if successful
        """
        cmd = ["git", "branch"]
        cmd.append("-D" if force else "-d")
        cmd.append(name)
        
        self._run_command(cmd)
        self.logger.info(f"Deleted branch: {name}")
        return True

    def branch_rename(self, old_name: str, new_name: str) -> bool:
        """
        Rename a branch.
        
        Args:
            old_name: Current branch name
            new_name: New branch name
            
        Returns:
            True if successful
        """
        self._run_command(["git", "branch", "-m", old_name, new_name])
        self.logger.info(f"Renamed branch {old_name} to {new_name}")
        return True

    def get_current_branch(self) -> str:
        """
        Get the current branch name.
        
        Returns:
            Current branch name
        """
        stdout, _, _ = self._run_command(["git", "branch", "--show-current"])
        return stdout

    def checkout(self, ref: str, create: bool = False, force: bool = False) -> bool:
        """
        Switch branches or restore working tree files.
        
        Args:
            ref: Branch name or commit to checkout
            create: Create new branch
            force: Force checkout
            
        Returns:
            True if successful
        """
        cmd = ["git", "checkout"]
        if create:
            cmd.append("-b")
        if force:
            cmd.append("-f")
        cmd.append(ref)
        
        self._run_command(cmd)
        self.logger.info(f"Checked out: {ref}")
        return True

    def switch(self, branch: str, create: bool = False) -> bool:
        """
        Switch to a branch.
        
        Args:
            branch: Branch name
            create: Create new branch
            
        Returns:
            True if successful
        """
        cmd = ["git", "switch"]
        if create:
            cmd.append("-c")
        cmd.append(branch)
        
        self._run_command(cmd)
        self.logger.info(f"Switched to branch: {branch}")
        return True

    # ==================== MERGE OPERATIONS ====================

    def merge(self, branch: str, no_ff: bool = False, squash: bool = False,
              message: Optional[str] = None) -> bool:
        """
        Merge a branch into current branch.
        
        Args:
            branch: Branch to merge
            no_ff: Create merge commit even for fast-forward
            squash: Squash commits
            message: Merge commit message
            
        Returns:
            True if successful
        """
        cmd = ["git", "merge"]
        if no_ff:
            cmd.append("--no-ff")
        if squash:
            cmd.append("--squash")
        if message:
            cmd.extend(["-m", message])
        cmd.append(branch)
        
        self._run_command(cmd)
        self.logger.info(f"Merged branch: {branch}")
        return True

    def merge_abort(self) -> bool:
        """
        Abort a merge in progress.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "merge", "--abort"])
        self.logger.info("Aborted merge")
        return True

    def is_merge_in_progress(self) -> bool:
        """
        Check if a merge is in progress.
        
        Returns:
            True if merge in progress
        """
        return (self.repo_path / ".git" / "MERGE_HEAD").exists()

    # ==================== REBASE OPERATIONS ====================

    def rebase(self, upstream: str, interactive: bool = False) -> bool:
        """
        Reapply commits on top of another base.
        
        Args:
            upstream: Upstream branch
            interactive: Interactive rebase
            
        Returns:
            True if successful
        """
        cmd = ["git", "rebase"]
        if interactive:
            cmd.append("-i")
        cmd.append(upstream)
        
        self._run_command(cmd)
        self.logger.info(f"Rebased onto: {upstream}")
        return True

    def rebase_continue(self) -> bool:
        """
        Continue a rebase after resolving conflicts.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "rebase", "--continue"])
        self.logger.info("Continued rebase")
        return True

    def rebase_abort(self) -> bool:
        """
        Abort a rebase in progress.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "rebase", "--abort"])
        self.logger.info("Aborted rebase")
        return True

    def rebase_skip(self) -> bool:
        """
        Skip current commit during rebase.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "rebase", "--skip"])
        self.logger.info("Skipped rebase commit")
        return True

    # ==================== REMOTE OPERATIONS ====================

    def remote_list(self, verbose: bool = False) -> List[str]:
        """
        List remote repositories.
        
        Args:
            verbose: Show URLs
            
        Returns:
            List of remotes
        """
        cmd = ["git", "remote"]
        if verbose:
            cmd.append("-v")
        
        stdout, _, _ = self._run_command(cmd)
        return [line for line in stdout.split("\n") if line]

    def remote_add(self, name: str, url: str) -> bool:
        """
        Add a remote repository.
        
        Args:
            name: Remote name
            url: Remote URL
            
        Returns:
            True if successful
        """
        self._run_command(["git", "remote", "add", name, url])
        self.logger.info(f"Added remote {name}: {url}")
        return True

    def remote_remove(self, name: str) -> bool:
        """
        Remove a remote repository.
        
        Args:
            name: Remote name
            
        Returns:
            True if successful
        """
        self._run_command(["git", "remote", "remove", name])
        self.logger.info(f"Removed remote: {name}")
        return True

    def remote_rename(self, old_name: str, new_name: str) -> bool:
        """
        Rename a remote.
        
        Args:
            old_name: Current remote name
            new_name: New remote name
            
        Returns:
            True if successful
        """
        self._run_command(["git", "remote", "rename", old_name, new_name])
        self.logger.info(f"Renamed remote {old_name} to {new_name}")
        return True

    def remote_get_url(self, name: str) -> str:
        """
        Get the URL of a remote.
        
        Args:
            name: Remote name
            
        Returns:
            Remote URL
        """
        stdout, _, _ = self._run_command(["git", "remote", "get-url", name])
        return stdout

    def remote_set_url(self, name: str, url: str) -> bool:
        """
        Set the URL of a remote.
        
        Args:
            name: Remote name
            url: New URL
            
        Returns:
            True if successful
        """
        self._run_command(["git", "remote", "set-url", name, url])
        self.logger.info(f"Set URL for remote {name}: {url}")
        return True

    def fetch(self, remote: str = "origin", prune: bool = False, 
              all_remotes: bool = False) -> bool:
        """
        Download objects and refs from remote repository.
        
        Args:
            remote: Remote name
            prune: Remove remote-tracking references
            all_remotes: Fetch all remotes
            
        Returns:
            True if successful
        """
        cmd = ["git", "fetch"]
        if all_remotes:
            cmd.append("--all")
        else:
            cmd.append(remote)
        if prune:
            cmd.append("--prune")
        
        self._run_command(cmd)
        self.logger.info(f"Fetched from remote: {remote}")
        return True

    def pull(self, remote: str = "origin", branch: Optional[str] = None,
             rebase: bool = False) -> bool:
        """
        Fetch and integrate with another repository.
        
        Args:
            remote: Remote name
            branch: Branch to pull
            rebase: Rebase instead of merge
            
        Returns:
            True if successful
        """
        cmd = ["git", "pull"]
        if rebase:
            cmd.append("--rebase")
        cmd.append(remote)
        if branch:
            cmd.append(branch)
        
        self._run_command(cmd)
        self.logger.info(f"Pulled from {remote}")
        return True

    def push(self, remote: str = "origin", branch: Optional[str] = None,
             force: bool = False, set_upstream: bool = False, 
             all_branches: bool = False, tags: bool = False) -> bool:
        """
        Update remote refs along with associated objects.
        
        Args:
            remote: Remote name
            branch: Branch to push
            force: Force push
            set_upstream: Set upstream for branch
            all_branches: Push all branches
            tags: Push tags
            
        Returns:
            True if successful
        """
        cmd = ["git", "push"]
        if force:
            cmd.append("--force")
        if set_upstream:
            cmd.append("--set-upstream")
        if all_branches:
            cmd.append("--all")
        if tags:
            cmd.append("--tags")
        
        cmd.append(remote)
        if branch and not all_branches:
            cmd.append(branch)
        
        self._run_command(cmd)
        self.logger.info(f"Pushed to {remote}")
        return True

    # ==================== LOG AND HISTORY ====================

    def log(self, max_count: Optional[int] = None, oneline: bool = False,
            graph: bool = False, all_branches: bool = False) -> str:
        """
        Show commit logs.
        
        Args:
            max_count: Limit number of commits
            oneline: Condensed format
            graph: Show graph
            all_branches: Show all branches
            
        Returns:
            Log output
        """
        cmd = ["git", "log"]
        if max_count:
            cmd.extend(["-n", str(max_count)])
        if oneline:
            cmd.append("--oneline")
        if graph:
            cmd.append("--graph")
        if all_branches:
            cmd.append("--all")
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    def log_json(self, max_count: Optional[int] = None) -> List[Dict]:
        """
        Get commit history in JSON format.
        
        Args:
            max_count: Limit number of commits
            
        Returns:
            List of commit dictionaries
        """
        cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%at|%s"]
        if max_count:
            cmd.extend(["-n", str(max_count)])
        
        stdout, _, _ = self._run_command(cmd)
        commits = []
        for line in stdout.split("\n"):
            if line:
                parts = line.split("|")
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "timestamp": int(parts[3]),
                    "message": parts[4] if len(parts) > 4 else ""
                })
        return commits

    def reflog(self, max_count: Optional[int] = None) -> str:
        """
        Show reference logs.
        
        Args:
            max_count: Limit number of entries
            
        Returns:
            Reflog output
        """
        cmd = ["git", "reflog"]
        if max_count:
            cmd.extend(["-n", str(max_count)])
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    def get_commit_count(self) -> int:
        """
        Get total number of commits.
        
        Returns:
            Commit count
        """
        stdout, _, code = self._run_command(
            ["git", "rev-list", "--count", "HEAD"], 
            check=False
        )
        return int(stdout) if code == 0 else 0

    def get_current_commit(self) -> str:
        """
        Get current commit hash.
        
        Returns:
            Commit hash
        """
        stdout, _, _ = self._run_command(["git", "rev-parse", "HEAD"])
        return stdout

    def get_commit_message(self, ref: str = "HEAD") -> str:
        """
        Get commit message.
        
        Args:
            ref: Commit reference
            
        Returns:
            Commit message
        """
        stdout, _, _ = self._run_command(
            ["git", "log", "-1", "--pretty=%B", ref]
        )
        return stdout

    # ==================== TAG OPERATIONS ====================

    def tag_list(self) -> List[str]:
        """
        List all tags.
        
        Returns:
            List of tag names
        """
        stdout, _, _ = self._run_command(["git", "tag"])
        return [tag for tag in stdout.split("\n") if tag]

    def tag_create(self, name: str, ref: str = "HEAD", 
                   message: Optional[str] = None) -> bool:
        """
        Create a tag.
        
        Args:
            name: Tag name
            ref: Reference to tag
            message: Annotated tag message
            
        Returns:
            True if successful
        """
        cmd = ["git", "tag"]
        if message:
            cmd.extend(["-a", name, "-m", message, ref])
        else:
            cmd.extend([name, ref])
        
        self._run_command(cmd)
        self.logger.info(f"Created tag: {name}")
        return True

    def tag_delete(self, name: str) -> bool:
        """
        Delete a tag.
        
        Args:
            name: Tag name
            
        Returns:
            True if successful
        """
        self._run_command(["git", "tag", "-d", name])
        self.logger.info(f"Deleted tag: {name}")
        return True

    def tag_push(self, remote: str = "origin", tag: Optional[str] = None) -> bool:
        """
        Push tags to remote.
        
        Args:
            remote: Remote name
            tag: Specific tag (None for all tags)
            
        Returns:
            True if successful
        """
        cmd = ["git", "push", remote]
        if tag:
            cmd.append(tag)
        else:
            cmd.append("--tags")
        
        self._run_command(cmd)
        self.logger.info(f"Pushed tags to {remote}")
        return True

    # ==================== STASH OPERATIONS ====================

    def stash_save(self, message: Optional[str] = None, 
                   include_untracked: bool = False) -> bool:
        """
        Save changes to stash.
        
        Args:
            message: Stash message
            include_untracked: Include untracked files
            
        Returns:
            True if successful
        """
        cmd = ["git", "stash", "push"]
        if message:
            cmd.extend(["-m", message])
        if include_untracked:
            cmd.append("-u")
        
        self._run_command(cmd)
        self.logger.info("Saved changes to stash")
        return True

    def stash_list(self) -> List[str]:
        """
        List stash entries.
        
        Returns:
            List of stash entries
        """
        stdout, _, _ = self._run_command(["git", "stash", "list"])
        return [line for line in stdout.split("\n") if line]

    def stash_pop(self, index: int = 0) -> bool:
        """
        Apply and remove a stash entry.
        
        Args:
            index: Stash index
            
        Returns:
            True if successful
        """
        self._run_command(["git", "stash", "pop", f"stash@{{{index}}}"])
        self.logger.info(f"Popped stash@{{{index}}}")
        return True

    def stash_apply(self, index: int = 0) -> bool:
        """
        Apply a stash entry without removing it.
        
        Args:
            index: Stash index
            
        Returns:
            True if successful
        """
        self._run_command(["git", "stash", "apply", f"stash@{{{index}}}"])
        self.logger.info(f"Applied stash@{{{index}}}")
        return True

    def stash_drop(self, index: int = 0) -> bool:
        """
        Remove a stash entry.
        
        Args:
            index: Stash index
            
        Returns:
            True if successful
        """
        self._run_command(["git", "stash", "drop", f"stash@{{{index}}}"])
        self.logger.info(f"Dropped stash@{{{index}}}")
        return True

    def stash_clear(self) -> bool:
        """
        Remove all stash entries.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "stash", "clear"])
        self.logger.info("Cleared all stash entries")
        return True

    # ==================== RESET OPERATIONS ====================

    def reset(self, mode: str = "mixed", ref: str = "HEAD") -> bool:
        """
        Reset current HEAD to specified state.
        
        Args:
            mode: Reset mode (soft, mixed, hard)
            ref: Reference to reset to
            
        Returns:
            True if successful
        """
        modes = {"soft": "--soft", "mixed": "--mixed", "hard": "--hard"}
        cmd = ["git", "reset", modes.get(mode, "--mixed"), ref]
        
        self._run_command(cmd)
        self.logger.info(f"Reset to {ref} ({mode})")
        return True

    def reset_hard(self, ref: str = "HEAD") -> bool:
        """
        Hard reset to specified reference.
        
        Args:
            ref: Reference to reset to
            
        Returns:
            True if successful
        """
        return self.reset(mode="hard", ref=ref)

    def reset_soft(self, ref: str = "HEAD") -> bool:
        """
        Soft reset to specified reference.
        
        Args:
            ref: Reference to reset to
            
        Returns:
            True if successful
        """
        return self.reset(mode="soft", ref=ref)

    # ==================== CHERRY-PICK ====================

    def cherry_pick(self, commit: str, no_commit: bool = False) -> bool:
        """
        Apply changes from an existing commit.
        
        Args:
            commit: Commit hash to cherry-pick
            no_commit: Apply without committing
            
        Returns:
            True if successful
        """
        cmd = ["git", "cherry-pick"]
        if no_commit:
            cmd.append("--no-commit")
        cmd.append(commit)
        
        self._run_command(cmd)
        self.logger.info(f"Cherry-picked commit: {commit}")
        return True

    def cherry_pick_abort(self) -> bool:
        """
        Cancel cherry-pick operation.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "cherry-pick", "--abort"])
        self.logger.info("Aborted cherry-pick")
        return True

    def cherry_pick_continue(self) -> bool:
        """
        Continue cherry-pick after resolving conflicts.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "cherry-pick", "--continue"])
        self.logger.info("Continued cherry-pick")
        return True

    # ==================== REVERT ====================

    def revert(self, commit: str, no_commit: bool = False) -> bool:
        """
        Revert an existing commit.
        
        Args:
            commit: Commit hash to revert
            no_commit: Revert without committing
            
        Returns:
            True if successful
        """
        cmd = ["git", "revert"]
        if no_commit:
            cmd.append("--no-commit")
        cmd.append(commit)
        
        self._run_command(cmd)
        self.logger.info(f"Reverted commit: {commit}")
        return True

    # ==================== CLEAN ====================

    def clean(self, force: bool = True, directories: bool = False, 
              dry_run: bool = False, ignored: bool = False) -> str:
        """
        Remove untracked files.
        
        Args:
            force: Force clean
            directories: Remove directories
            dry_run: Show what would be deleted
            ignored: Remove ignored files
            
        Returns:
            Output of clean operation
        """
        cmd = ["git", "clean"]
        if dry_run:
            cmd.append("-n")
        if force and not dry_run:
            cmd.append("-f")
        if directories:
            cmd.append("-d")
        if ignored:
            cmd.append("-x")
        
        stdout, _, _ = self._run_command(cmd)
        self.logger.info("Cleaned untracked files")
        return stdout

    # ==================== SUBMODULE OPERATIONS ====================

    def submodule_add(self, url: str, path: str, branch: Optional[str] = None) -> bool:
        """
        Add a submodule.
        
        Args:
            url: Submodule repository URL
            path: Path where submodule will be placed
            branch: Specific branch to track
            
        Returns:
            True if successful
        """
        cmd = ["git", "submodule", "add"]
        if branch:
            cmd.extend(["-b", branch])
        cmd.extend([url, path])
        
        self._run_command(cmd)
        self.logger.info(f"Added submodule: {path}")
        return True

    def submodule_init(self) -> bool:
        """
        Initialize submodules.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "submodule", "init"])
        self.logger.info("Initialized submodules")
        return True

    def submodule_update(self, init: bool = False, recursive: bool = False) -> bool:
        """
        Update submodules.
        
        Args:
            init: Initialize submodules
            recursive: Update recursively
            
        Returns:
            True if successful
        """
        cmd = ["git", "submodule", "update"]
        if init:
            cmd.append("--init")
        if recursive:
            cmd.append("--recursive")
        
        self._run_command(cmd)
        self.logger.info("Updated submodules")
        return True

    def submodule_list(self) -> List[Dict[str, str]]:
        """
        List submodules.
        
        Returns:
            List of submodule information
        """
        stdout, _, code = self._run_command(
            ["git", "submodule", "status"], 
            check=False
        )
        if code != 0:
            return []
        
        submodules = []
        for line in stdout.split("\n"):
            if line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    submodules.append({
                        "commit": parts[0].lstrip("-+"),
                        "path": parts[1],
                        "branch": parts[2] if len(parts) > 2 else ""
                    })
        return submodules

    # ==================== BLAME ====================

    def blame(self, file: str, line_range: Optional[Tuple[int, int]] = None) -> str:
        """
        Show what revision and author last modified each line.
        
        Args:
            file: File to blame
            line_range: Optional tuple of (start_line, end_line)
            
        Returns:
            Blame output
        """
        cmd = ["git", "blame"]
        if line_range:
            cmd.extend(["-L", f"{line_range[0]},{line_range[1]}"])
        cmd.append(file)
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    # ==================== BISECT ====================

    def bisect_start(self) -> bool:
        """
        Start bisect session.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "bisect", "start"])
        self.logger.info("Started bisect")
        return True

    def bisect_bad(self, commit: Optional[str] = None) -> bool:
        """
        Mark commit as bad.
        
        Args:
            commit: Commit hash (None for current)
            
        Returns:
            True if successful
        """
        cmd = ["git", "bisect", "bad"]
        if commit:
            cmd.append(commit)
        
        self._run_command(cmd)
        self.logger.info(f"Marked as bad: {commit or 'current'}")
        return True

    def bisect_good(self, commit: Optional[str] = None) -> bool:
        """
        Mark commit as good.
        
        Args:
            commit: Commit hash (None for current)
            
        Returns:
            True if successful
        """
        cmd = ["git", "bisect", "good"]
        if commit:
            cmd.append(commit)
        
        self._run_command(cmd)
        self.logger.info(f"Marked as good: {commit or 'current'}")
        return True

    def bisect_reset(self) -> bool:
        """
        End bisect session.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "bisect", "reset"])
        self.logger.info("Reset bisect")
        return True

    # ==================== WORKTREE ====================

    def worktree_add(self, path: str, branch: Optional[str] = None) -> bool:
        """
        Create a new working tree.
        
        Args:
            path: Path for new worktree
            branch: Branch to checkout
            
        Returns:
            True if successful
        """
        cmd = ["git", "worktree", "add", path]
        if branch:
            cmd.append(branch)
        
        self._run_command(cmd)
        self.logger.info(f"Added worktree: {path}")
        return True

    def worktree_list(self) -> List[Dict[str, str]]:
        """
        List working trees.
        
        Returns:
            List of worktree information
        """
        stdout, _, _ = self._run_command(["git", "worktree", "list", "--porcelain"])
        worktrees = []
        current = {}
        
        for line in stdout.split("\n"):
            if not line:
                if current:
                    worktrees.append(current)
                    current = {}
            else:
                key, value = line.split(" ", 1) if " " in line else (line, "")
                current[key] = value
        
        if current:
            worktrees.append(current)
        
        return worktrees

    def worktree_remove(self, path: str, force: bool = False) -> bool:
        """
        Remove a working tree.
        
        Args:
            path: Worktree path
            force: Force removal
            
        Returns:
            True if successful
        """
        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(path)
        
        self._run_command(cmd)
        self.logger.info(f"Removed worktree: {path}")
        return True

    def worktree_prune(self) -> bool:
        """
        Remove worktree information for deleted working trees.
        
        Returns:
            True if successful
        """
        self._run_command(["git", "worktree", "prune"])
        self.logger.info("Pruned worktrees")
        return True

    # ==================== ARCHIVE ====================

    def archive(self, output_file: str, ref: str = "HEAD", 
                format: str = "zip") -> bool:
        """
        Create archive of files from a tree.
        
        Args:
            output_file: Output archive file
            ref: Tree reference
            format: Archive format (zip, tar, tar.gz)
            
        Returns:
            True if successful
        """
        cmd = ["git", "archive", f"--format={format}", 
               f"--output={output_file}", ref]
        
        self._run_command(cmd)
        self.logger.info(f"Created archive: {output_file}")
        return True

    # ==================== GREP ====================

    def grep(self, pattern: str, files: Optional[List[str]] = None,
             ignore_case: bool = False, line_number: bool = False) -> str:
        """
        Search for pattern in tracked files.
        
        Args:
            pattern: Pattern to search for
            files: Specific files to search
            ignore_case: Case-insensitive search
            line_number: Show line numbers
            
        Returns:
            Grep output
        """
        cmd = ["git", "grep"]
        if ignore_case:
            cmd.append("-i")
        if line_number:
            cmd.append("-n")
        cmd.append(pattern)
        if files:
            cmd.append("--")
            cmd.extend(files)
        
        stdout, _, code = self._run_command(cmd, check=False)
        return stdout if code == 0 else ""

    # ==================== SHORTLOG ====================

    def shortlog(self, summary: bool = True, numbered: bool = True) -> str:
        """
        Summarize git log output.
        
        Args:
            summary: Show only commit count
            numbered: Sort by number of commits
            
        Returns:
            Shortlog output
        """
        cmd = ["git", "shortlog"]
        if summary:
            cmd.append("-s")
        if numbered:
            cmd.append("-n")
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    # ==================== DESCRIBE ====================

    def describe(self, ref: str = "HEAD", tags: bool = True, 
                 abbrev: Optional[int] = None) -> str:
        """
        Give an object a human readable name based on refs.
        
        Args:
            ref: Reference to describe
            tags: Use any tag found in refs/tags
            abbrev: Use specified digits for abbreviated object name
            
        Returns:
            Description string
        """
        cmd = ["git", "describe"]
        if tags:
            cmd.append("--tags")
        if abbrev is not None:
            cmd.append(f"--abbrev={abbrev}")
        cmd.append(ref)
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    # ==================== NOTES ====================

    def notes_add(self, message: str, ref: str = "HEAD") -> bool:
        """
        Add notes to an object.
        
        Args:
            message: Note message
            ref: Object reference
            
        Returns:
            True if successful
        """
        self._run_command(["git", "notes", "add", "-m", message, ref])
        self.logger.info(f"Added note to {ref}")
        return True

    def notes_show(self, ref: str = "HEAD") -> str:
        """
        Show notes for an object.
        
        Args:
            ref: Object reference
            
        Returns:
            Notes content
        """
        stdout, _, code = self._run_command(
            ["git", "notes", "show", ref], 
            check=False
        )
        return stdout if code == 0 else ""

    def notes_remove(self, ref: str = "HEAD") -> bool:
        """
        Remove notes from an object.
        
        Args:
            ref: Object reference
            
        Returns:
            True if successful
        """
        self._run_command(["git", "notes", "remove", ref])
        self.logger.info(f"Removed note from {ref}")
        return True

    # ==================== LS-FILES ====================

    def ls_files(self, cached: bool = True, modified: bool = False,
                 others: bool = False, ignored: bool = False) -> List[str]:
        """
        Show information about files in the index and working tree.
        
        Args:
            cached: Show cached files
            modified: Show modified files
            others: Show untracked files
            ignored: Show ignored files
            
        Returns:
            List of file paths
        """
        cmd = ["git", "ls-files"]
        if cached:
            cmd.append("--cached")
        if modified:
            cmd.append("--modified")
        if others:
            cmd.append("--others")
        if ignored:
            cmd.append("--ignored")
        
        stdout, _, _ = self._run_command(cmd)
        return [f for f in stdout.split("\n") if f]

    # ==================== REV-PARSE ====================

    def rev_parse(self, ref: str, short: bool = False) -> str:
        """
        Parse revision to SHA-1.
        
        Args:
            ref: Reference to parse
            short: Output short SHA
            
        Returns:
            SHA-1 hash
        """
        cmd = ["git", "rev-parse"]
        if short:
            cmd.append("--short")
        cmd.append(ref)
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    def is_ancestor(self, commit1: str, commit2: str) -> bool:
        """
        Check if commit1 is an ancestor of commit2.
        
        Args:
            commit1: Potential ancestor commit
            commit2: Commit to check
            
        Returns:
            True if commit1 is ancestor of commit2
        """
        _, _, code = self._run_command(
            ["git", "merge-base", "--is-ancestor", commit1, commit2],
            check=False
        )
        return code == 0

    # ==================== FSCK ====================

    def fsck(self, full: bool = False) -> str:
        """
        Verify the connectivity and validity of objects.
        
        Args:
            full: Check all objects
            
        Returns:
            Fsck output
        """
        cmd = ["git", "fsck"]
        if full:
            cmd.append("--full")
        
        stdout, _, _ = self._run_command(cmd)
        return stdout

    # ==================== GC ====================

    def gc(self, aggressive: bool = False, prune: bool = True) -> bool:
        """
        Cleanup unnecessary files and optimize repository.
        
        Args:
            aggressive: More aggressive optimization
            prune: Prune loose objects
            
        Returns:
            True if successful
        """
        cmd = ["git", "gc"]
        if aggressive:
            cmd.append("--aggressive")
        if prune:
            cmd.append("--prune=now")
        
        self._run_command(cmd)
        self.logger.info("Repository garbage collected")
        return True

    # ==================== MAINTENANCE ====================

    def count_objects(self, verbose: bool = True) -> Dict[str, Union[int, str]]:
        """
        Count unpacked objects and their disk consumption.
        
        Args:
            verbose: Show detailed information
            
        Returns:
            Dictionary with object statistics
        """
        cmd = ["git", "count-objects"]
        if verbose:
            cmd.append("-v")
        
        stdout, _, _ = self._run_command(cmd)
        stats = {}
        
        for line in stdout.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                stats[key.strip()] = value.strip()
        
        return stats

    def verify_pack(self) -> str:
        """
        Validate packed Git archive files.
        
        Returns:
            Verification output
        """
        pack_dir = self.repo_path / ".git" / "objects" / "pack"
        if not pack_dir.exists():
            return "No pack files found"
        
        pack_files = list(pack_dir.glob("*.idx"))
        if not pack_files:
            return "No pack files found"
        
        outputs = []
        for pack in pack_files:
            stdout, _, _ = self._run_command(["git", "verify-pack", "-v", str(pack)])
            outputs.append(stdout)
        
        return "\n".join(outputs)

    # ==================== HELP AND UTILITIES ====================

    def version(self) -> str:
        """
        Get Git version.
        
        Returns:
            Git version string
        """
        stdout, _, _ = self._run_command(["git", "--version"])
        return stdout

    def get_repo_root(self) -> Path:
        """
        Get the root directory of the repository.
        
        Returns:
            Path to repository root
        """
        stdout, _, _ = self._run_command(["git", "rev-parse", "--show-toplevel"])
        return Path(stdout)

    def get_git_dir(self) -> Path:
        """
        Get the .git directory path.
        
        Returns:
            Path to .git directory
        """
        stdout, _, _ = self._run_command(["git", "rev-parse", "--git-dir"])
        return Path(stdout)

    def is_inside_work_tree(self) -> bool:
        """
        Check if inside a Git work tree.
        
        Returns:
            True if inside work tree
        """
        stdout, _, code = self._run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=False
        )
        return code == 0 and stdout.lower() == "true"

    def is_bare_repository(self) -> bool:
        """
        Check if repository is bare.
        
        Returns:
            True if bare repository
        """
        stdout, _, code = self._run_command(
            ["git", "rev-parse", "--is-bare-repository"],
            check=False
        )
        return code == 0 and stdout.lower() == "true"

    def get_upstream_branch(self, branch: Optional[str] = None) -> Optional[str]:
        """
        Get the upstream branch for a local branch.
        
        Args:
            branch: Local branch (None for current)
            
        Returns:
            Upstream branch name or None
        """
        if not branch:
            branch = self.get_current_branch()
        
        stdout, _, code = self._run_command(
            ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
            check=False
        )
        return stdout if code == 0 else None

    def list_changed_files(self, commit1: str = "HEAD~1", 
                           commit2: str = "HEAD") -> List[str]:
        """
        List files changed between two commits.
        
        Args:
            commit1: First commit
            commit2: Second commit
            
        Returns:
            List of changed file paths
        """
        stdout, _, _ = self._run_command(
            ["git", "diff", "--name-only", commit1, commit2]
        )
        return [f for f in stdout.split("\n") if f]

    def get_file_history(self, file: str, max_count: Optional[int] = None) -> List[Dict]:
        """
        Get commit history for a specific file.
        
        Args:
            file: File path
            max_count: Maximum number of commits
            
        Returns:
            List of commit information
        """
        cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%at|%s", "--", file]
        if max_count:
            cmd.insert(2, f"-n{max_count}")
        
        stdout, _, _ = self._run_command(cmd)
        commits = []
        for line in stdout.split("\n"):
            if line:
                parts = line.split("|")
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "timestamp": int(parts[3]),
                    "message": parts[4] if len(parts) > 4 else ""
                })
        return commits

    def get_contributors(self) -> List[Dict[str, Union[str, int]]]:
        """
        Get list of contributors with commit counts.
        
        Returns:
            List of contributor information
        """
        stdout, _, _ = self._run_command(
            ["git", "shortlog", "-sne", "--all"]
        )
        contributors = []
        for line in stdout.split("\n"):
            if line:
                match = re.match(r'\s*(\d+)\s+(.+?)\s+<(.+?)>', line)
                if match:
                    contributors.append({
                        "commits": int(match.group(1)),
                        "name": match.group(2),
                        "email": match.group(3)
                    })
        return contributors

    def get_file_at_commit(self, file: str, commit: str = "HEAD") -> str:
        """
        Get file content at a specific commit.
        
        Args:
            file: File path
            commit: Commit reference
            
        Returns:
            File content
        """
        stdout, _, _ = self._run_command(["git", "show", f"{commit}:{file}"])
        return stdout

    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.
        
        Returns:
            True if there are uncommitted changes
        """
        stdout, _, _ = self._run_command(["git", "status", "--porcelain"])
        return bool(stdout.strip())

    def has_untracked_files(self) -> bool:
        """
        Check if there are untracked files.
        
        Returns:
            True if there are untracked files
        """
        statuses = self.status_porcelain()
        return any(s["index"] == "?" for s in statuses)