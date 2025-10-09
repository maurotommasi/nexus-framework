# Enterprise Git Manager

A comprehensive, enterprise-level Python wrapper for Git operations providing 100+ functions with robust error handling, logging, and validation.

## Features

- **100+ Git Operations**: Complete coverage of Git functionality
- **Enterprise-Grade**: Built for production environments with proper error handling
- **Type Hints**: Full type annotation support for better IDE integration
- **Comprehensive Logging**: Built-in logging for debugging and auditing
- **Clean API**: Intuitive, Pythonic interface for all Git operations
- **Error Handling**: Robust exception handling with detailed error messages

## Installation

### Prerequisites

- Python 3.7+
- Git installed and accessible in PATH

### Setup

```python
from git_manager import GitManager

# Initialize with current directory
git = GitManager()

# Or specify a repository path
git = GitManager(repo_path="/path/to/repo")

# With custom logging level
import logging
git = GitManager(repo_path="/path/to/repo", log_level=logging.DEBUG)
```

## Quick Start

```python
from git_manager import GitManager

# Initialize manager
git = GitManager()

# Add files and commit
git.add_all()
git.commit("Initial commit")

# Create and switch to new branch
git.branch_create("feature/new-feature")
git.checkout("feature/new-feature")

# Push to remote
git.push(remote="origin", branch="feature/new-feature", set_upstream=True)
```

## API Reference

### Repository Initialization

#### `init(bare=False, initial_branch=None)`
Initialize a new Git repository.

**Input:**
- `bare` (bool): Create a bare repository (default: False)
- `initial_branch` (str, optional): Name of the initial branch

**Output:**
- Returns `True` on success

**Example:**
```python
git.init(initial_branch="main")
```

#### `clone(url, target_dir=None, depth=None, branch=None)`
Clone a repository.

**Input:**
- `url` (str): Repository URL to clone
- `target_dir` (str, optional): Target directory for clone
- `depth` (int, optional): Create shallow clone with specified depth
- `branch` (str, optional): Clone specific branch

**Output:**
- Returns `True` on success

**Example:**
```python
git.clone("https://github.com/user/repo.git", depth=1, branch="main")
```

### Configuration

#### `config_set(key, value, global_config=False)`
Set a configuration value.

**Input:**
- `key` (str): Configuration key (e.g., "user.name")
- `value` (str): Configuration value
- `global_config` (bool): Set globally instead of locally

**Output:**
- Returns `True` on success

**Example:**
```python
git.config_set("user.name", "John Doe")
git.config_set("user.email", "john@example.com", global_config=True)
```

#### `config_get(key, global_config=False)`
Get a configuration value.

**Input:**
- `key` (str): Configuration key
- `global_config` (bool): Get from global config

**Output:**
- Returns configuration value (str) or `None`

**Example:**
```python
name = git.config_get("user.name")
```

#### `config_list(global_config=False)`
List all configuration values.

**Input:**
- `global_config` (bool): List global config

**Output:**
- Returns dictionary of configuration key-value pairs

**Example:**
```python
config = git.config_list()
# {'user.name': 'John Doe', 'user.email': 'john@example.com', ...}
```

#### `config_unset(key, global_config=False)`
Unset a configuration value.

**Input:**
- `key` (str): Configuration key to unset
- `global_config` (bool): Unset from global config

**Output:**
- Returns `True` on success

**Example:**
```python
git.config_unset("user.nickname")
```

### File Operations

#### `add(files, force=False)`
Add files to staging area.

**Input:**
- `files` (str or list): File path(s) to add
- `force` (bool): Force add ignored files

**Output:**
- Returns `True` on success

**Example:**
```python
git.add("file.txt")
git.add(["file1.txt", "file2.txt"])
git.add("*.pyc", force=True)
```

#### `add_all()`
Add all changes to staging area.

**Output:**
- Returns `True` on success

**Example:**
```python
git.add_all()
```

#### `rm(files, force=False, cached=False)`
Remove files from working tree and index.

**Input:**
- `files` (str or list): File path(s) to remove
- `force` (bool): Force removal
- `cached` (bool): Only remove from index, keep in working directory

**Output:**
- Returns `True` on success

**Example:**
```python
git.rm("old_file.txt")
git.rm("secret.txt", cached=True)  # Remove from Git but keep local
```

#### `mv(source, destination, force=False)`
Move or rename a file.

**Input:**
- `source` (str): Source path
- `destination` (str): Destination path
- `force` (bool): Force move/rename

**Output:**
- Returns `True` on success

**Example:**
```python
git.mv("old_name.txt", "new_name.txt")
```

#### `restore(files, staged=False)`
Restore working tree files.

**Input:**
- `files` (str or list): File path(s) to restore
- `staged` (bool): Restore staged files

**Output:**
- Returns `True` on success

**Example:**
```python
git.restore("file.txt")  # Discard working directory changes
git.restore("file.txt", staged=True)  # Unstage file
```

### Commit Operations

#### `commit(message, amend=False, all_changes=False, allow_empty=False)`
Create a commit.

**Input:**
- `message` (str): Commit message
- `amend` (bool): Amend previous commit
- `all_changes` (bool): Automatically stage modified and deleted files
- `allow_empty` (bool): Allow empty commit

**Output:**
- Returns commit hash (str)

**Example:**
```python
hash = git.commit("Add new feature")
hash = git.commit("Update documentation", all_changes=True)
```

#### `commit_with_files(message, files)`
Add specific files and commit.

**Input:**
- `message` (str): Commit message
- `files` (list): List of files to commit

**Output:**
- Returns commit hash (str)

**Example:**
```python
git.commit_with_files("Update config", ["config.yml", "settings.py"])
```

#### `amend_commit(message=None)`
Amend the last commit.

**Input:**
- `message` (str, optional): New commit message (None to keep existing)

**Output:**
- Returns commit hash (str)

**Example:**
```python
git.amend_commit("Fixed typo in commit message")
git.amend_commit()  # Keep same message
```

### Status and Inspection

#### `status(short=False)`
Get repository status.

**Input:**
- `short` (bool): Use short format

**Output:**
- Returns status output (str)

**Example:**
```python
status = git.status()
print(status)
```

#### `status_porcelain()`
Get status in machine-readable format.

**Output:**
- Returns list of dictionaries with status information

**Example:**
```python
statuses = git.status_porcelain()
# [{'index': 'M', 'worktree': ' ', 'file': 'file.txt'}, ...]
```

#### `diff(commit1=None, commit2=None, files=None, staged=False)`
Show changes between commits, working tree, etc.

**Input:**
- `commit1` (str, optional): First commit to compare
- `commit2` (str, optional): Second commit to compare
- `files` (list, optional): Specific files to diff
- `staged` (bool): Show staged changes

**Output:**
- Returns diff output (str)

**Example:**
```python
diff = git.diff()  # Unstaged changes
diff = git.diff(staged=True)  # Staged changes
diff = git.diff("HEAD~1", "HEAD")  # Between commits
```

#### `diff_stat(commit1=None, commit2=None)`
Show diff statistics.

**Input:**
- `commit1` (str, optional): First commit
- `commit2` (str, optional): Second commit

**Output:**
- Returns diff statistics (str)

**Example:**
```python
stats = git.diff_stat("HEAD~5", "HEAD")
```

#### `show(ref="HEAD")`
Show various types of objects.

**Input:**
- `ref` (str): Reference to show (default: HEAD)

**Output:**
- Returns object information (str)

**Example:**
```python
info = git.show("HEAD")
info = git.show("v1.0.0")
```

### Branch Operations

#### `branch_list(remote=False, all_branches=False)`
List branches.

**Input:**
- `remote` (bool): List remote branches
- `all_branches` (bool): List all branches (local and remote)

**Output:**
- Returns list of branch names

**Example:**
```python
branches = git.branch_list()
remote_branches = git.branch_list(remote=True)
all_branches = git.branch_list(all_branches=True)
```

#### `branch_create(name, start_point=None)`
Create a new branch.

**Input:**
- `name` (str): Branch name
- `start_point` (str, optional): Starting point for new branch

**Output:**
- Returns `True` on success

**Example:**
```python
git.branch_create("feature/login")
git.branch_create("hotfix", start_point="v1.0.0")
```

#### `branch_delete(name, force=False)`
Delete a branch.

**Input:**
- `name` (str): Branch name
- `force` (bool): Force deletion

**Output:**
- Returns `True` on success

**Example:**
```python
git.branch_delete("old-feature")
git.branch_delete("unmerged-branch", force=True)
```

#### `branch_rename(old_name, new_name)`
Rename a branch.

**Input:**
- `old_name` (str): Current branch name
- `new_name` (str): New branch name

**Output:**
- Returns `True` on success

**Example:**
```python
git.branch_rename("old-name", "new-name")
```

#### `get_current_branch()`
Get the current branch name.

**Output:**
- Returns current branch name (str)

**Example:**
```python
branch = git.get_current_branch()
```

#### `checkout(ref, create=False, force=False)`
Switch branches or restore working tree files.

**Input:**
- `ref` (str): Branch name or commit to checkout
- `create` (bool): Create new branch
- `force` (bool): Force checkout

**Output:**
- Returns `True` on success

**Example:**
```python
git.checkout("main")
git.checkout("feature/new", create=True)
```

#### `switch(branch, create=False)`
Switch to a branch (modern alternative to checkout).

**Input:**
- `branch` (str): Branch name
- `create` (bool): Create new branch

**Output:**
- Returns `True` on success

**Example:**
```python
git.switch("develop")
git.switch("feature/test", create=True)
```

### Merge Operations

#### `merge(branch, no_ff=False, squash=False, message=None)`
Merge a branch into current branch.

**Input:**
- `branch` (str): Branch to merge
- `no_ff` (bool): Create merge commit even for fast-forward
- `squash` (bool): Squash commits
- `message` (str, optional): Merge commit message

**Output:**
- Returns `True` on success

**Example:**
```python
git.merge("feature/login")
git.merge("hotfix", no_ff=True)
git.merge("feature", squash=True, message="Squashed feature commits")
```

#### `merge_abort()`
Abort a merge in progress.

**Output:**
- Returns `True` on success

**Example:**
```python
git.merge_abort()
```

#### `is_merge_in_progress()`
Check if a merge is in progress.

**Output:**
- Returns `True` if merge in progress

**Example:**
```python
if git.is_merge_in_progress():
    print("Merge conflicts need resolution")
```

### Rebase Operations

#### `rebase(upstream, interactive=False)`
Reapply commits on top of another base.

**Input:**
- `upstream` (str): Upstream branch
- `interactive` (bool): Interactive rebase

**Output:**
- Returns `True` on success

**Example:**
```python
git.rebase("main")
git.rebase("main", interactive=True)
```

#### `rebase_continue()`
Continue a rebase after resolving conflicts.

**Output:**
- Returns `True` on success

**Example:**
```python
# After resolving conflicts
git.add_all()
git.rebase_continue()
```

#### `rebase_abort()`
Abort a rebase in progress.

**Output:**
- Returns `True` on success

**Example:**
```python
git.rebase_abort()
```

#### `rebase_skip()`
Skip current commit during rebase.

**Output:**
- Returns `True` on success

**Example:**
```python
git.rebase_skip()
```

### Remote Operations

#### `remote_list(verbose=False)`
List remote repositories.

**Input:**
- `verbose` (bool): Show URLs

**Output:**
- Returns list of remotes

**Example:**
```python
remotes = git.remote_list()
remotes_with_urls = git.remote_list(verbose=True)
```

#### `remote_add(name, url)`
Add a remote repository.

**Input:**
- `name` (str): Remote name
- `url` (str): Remote URL

**Output:**
- Returns `True` on success

**Example:**
```python
git.remote_add("origin", "https://github.com/user/repo.git")
```

#### `remote_remove(name)`
Remove a remote repository.

**Input:**
- `name` (str): Remote name

**Output:**
- Returns `True` on success

**Example:**
```python
git.remote_remove("old-origin")
```

#### `remote_rename(old_name, new_name)`
Rename a remote.

**Input:**
- `old_name` (str): Current remote name
- `new_name` (str): New remote name

**Output:**
- Returns `True` on success

**Example:**
```python
git.remote_rename("origin", "upstream")
```

#### `remote_get_url(name)`
Get the URL of a remote.

**Input:**
- `name` (str): Remote name

**Output:**
- Returns remote URL (str)

**Example:**
```python
url = git.remote_get_url("origin")
```

#### `remote_set_url(name, url)`
Set the URL of a remote.

**Input:**
- `name` (str): Remote name
- `url` (str): New URL

**Output:**
- Returns `True` on success

**Example:**
```python
git.remote_set_url("origin", "git@github.com:user/repo.git")
```

#### `fetch(remote="origin", prune=False, all_remotes=False)`
Download objects and refs from remote repository.

**Input:**
- `remote` (str): Remote name (default: "origin")
- `prune` (bool): Remove remote-tracking references
- `all_remotes` (bool): Fetch all remotes

**Output:**
- Returns `True` on success

**Example:**
```python
git.fetch()
git.fetch(prune=True)
git.fetch(all_remotes=True)
```

#### `pull(remote="origin", branch=None, rebase=False)`
Fetch and integrate with another repository.

**Input:**
- `remote` (str): Remote name (default: "origin")
- `branch` (str, optional): Branch to pull
- `rebase` (bool): Rebase instead of merge

**Output:**
- Returns `True` on success

**Example:**
```python
git.pull()
git.pull(branch="main", rebase=True)
```

#### `push(remote="origin", branch=None, force=False, set_upstream=False, all_branches=False, tags=False)`
Update remote refs along with associated objects.

**Input:**
- `remote` (str): Remote name (default: "origin")
- `branch` (str, optional): Branch to push
- `force` (bool): Force push
- `set_upstream` (bool): Set upstream for branch
- `all_branches` (bool): Push all branches
- `tags` (bool): Push tags

**Output:**
- Returns `True` on success

**Example:**
```python
git.push()
git.push(branch="feature", set_upstream=True)
git.push(force=True)
git.push(tags=True)
```

### Log and History

#### `log(max_count=None, oneline=False, graph=False, all_branches=False)`
Show commit logs.

**Input:**
- `max_count` (int, optional): Limit number of commits
- `oneline` (bool): Condensed format
- `graph` (bool): Show graph
- `all_branches` (bool): Show all branches

**Output:**
- Returns log output (str)

**Example:**
```python
log = git.log(max_count=10, oneline=True)
log = git.log(graph=True, all_branches=True)
```

#### `log_json(max_count=None)`
Get commit history in JSON format.

**Input:**
- `max_count` (int, optional): Limit number of commits

**Output:**
- Returns list of commit dictionaries

**Example:**
```python
commits = git.log_json(max_count=5)
# [{'hash': 'abc123', 'author': 'John', 'email': 'john@example.com', 
#   'timestamp': 1234567890, 'message': 'Initial commit'}, ...]
```

#### `reflog(max_count=None)`
Show reference logs.

**Input:**
- `max_count` (int, optional): Limit number of entries

**Output:**
- Returns reflog output (str)

**Example:**
```python
reflog = git.reflog(max_count=20)
```

#### `get_commit_count()`
Get total number of commits.

**Output:**
- Returns commit count (int)

**Example:**
```python
count = git.get_commit_count()
```

#### `get_current_commit()`
Get current commit hash.

**Output:**
- Returns commit hash (str)

**Example:**
```python
current = git.get_current_commit()
```

#### `get_commit_message(ref="HEAD")`
Get commit message.

**Input:**
- `ref` (str): Commit reference (default: "HEAD")

**Output:**
- Returns commit message (str)

**Example:**
```python
message = git.get_commit_message()
message = git.get_commit_message("HEAD~3")
```

### Tag Operations

#### `tag_list()`
List all tags.

**Output:**
- Returns list of tag names

**Example:**
```python
tags = git.tag_list()
```

#### `tag_create(name, ref="HEAD", message=None)`
Create a tag.

**Input:**
- `name` (str): Tag name
- `ref` (str): Reference to tag (default: "HEAD")
- `message` (str, optional): Annotated tag message

**Output:**
- Returns `True` on success

**Example:**
```python
git.tag_create("v1.0.0")
git.tag_create("v1.0.0", message="Release version 1.0.0")
```

#### `tag_delete(name)`
Delete a tag.

**Input:**
- `name` (str): Tag name

**Output:**
- Returns `True` on success

**Example:**
```python
git.tag_delete("v0.9.0")
```

#### `tag_push(remote="origin", tag=None)`
Push tags to remote.

**Input:**
- `remote` (str): Remote name (default: "origin")
- `tag` (str, optional): Specific tag (None for all tags)

**Output:**
- Returns `True` on success

**Example:**
```python
git.tag_push()  # Push all tags
git.tag_push(tag="v1.0.0")  # Push specific tag
```

### Stash Operations

#### `stash_save(message=None, include_untracked=False)`
Save changes to stash.

**Input:**
- `message` (str, optional): Stash message
- `include_untracked` (bool): Include untracked files

**Output:**
- Returns `True` on success

**Example:**
```python
git.stash_save()
git.stash_save("WIP: feature implementation", include_untracked=True)
```

#### `stash_list()`
List stash entries.

**Output:**
- Returns list of stash entries

**Example:**
```python
stashes = git.stash_list()
```

#### `stash_pop(index=0)`
Apply and remove a stash entry.

**Input:**
- `index` (int): Stash index (default: 0)

**Output:**
- Returns `True` on success

**Example:**
```python
git.stash_pop()
git.stash_pop(index=2)
```

#### `stash_apply(index=0)`
Apply a stash entry without removing it.

**Input:**
- `index` (int): Stash index (default: 0)

**Output:**
- Returns `True` on success

**Example:**
```python
git.stash_apply()
```

#### `stash_drop(index=0)`
Remove a stash entry.

**Input:**
- `index` (int): Stash index (default: 0)

**Output:**
- Returns `True` on success

**Example:**
```python
git.stash_drop(index=1)
```

#### `stash_clear()`
Remove all stash entries.

**Output:**
- Returns `True` on success

**Example:**
```python
git.stash_clear()
```

### Reset Operations

#### `reset(mode="mixed", ref="HEAD")`
Reset current HEAD to specified state.

**Input:**
- `mode` (str): Reset mode ("soft", "mixed", "hard")
- `ref` (str): Reference to reset to (default: "HEAD")

**Output:**
- Returns `True` on success

**Example:**
```python
git.reset(mode="soft", ref="HEAD~1")
git.reset(mode="hard", ref="origin/main")
```

#### `reset_hard(ref="HEAD")`
Hard reset to specified reference.

**Input:**
- `ref` (str): Reference to reset to (default: "HEAD")

**Output:**
- Returns `True` on success

**Example:**
```python
git.reset_hard("HEAD~2")
```

#### `reset_soft(ref="HEAD")`
Soft reset to specified reference.

**Input:**
- `ref` (str): Reference to reset to (default: "HEAD")

**Output:**
- Returns `True` on success

**Example:**
```python
git.reset_soft("HEAD~1")
```

### Cherry-Pick Operations

#### `cherry_pick(commit, no_commit=False)`
Apply changes from an existing commit.

**Input:**
- `commit` (str): Commit hash to cherry-pick
- `no_commit` (bool): Apply without committing

**Output:**
- Returns `True` on success

**Example:**
```python
git.cherry_pick("abc123")
git.cherry_pick("def456", no_commit=True)
```

#### `cherry_pick_abort()`
Cancel cherry-pick operation.

**Output:**
- Returns `True` on success

#### `cherry_pick_continue()`
Continue cherry-pick after resolving conflicts.

**Output:**
- Returns `True` on success

### Revert Operations

#### `revert(commit, no_commit=False)`
Revert an existing commit.

**Input:**
- `commit` (str): Commit hash to revert
- `no_commit` (bool): Revert without committing

**Output:**
- Returns `True` on success

**Example:**
```python
git.revert("abc123")
```

### Clean Operations

#### `clean(force=True, directories=False, dry_run=False, ignored=False)`
Remove untracked files.

**Input:**
- `force` (bool): Force clean (default: True)
- `directories` (bool): Remove directories
- `dry_run` (bool): Show what would be deleted
- `ignored` (bool): Remove ignored files

**Output:**
- Returns output of clean operation (str)

**Example:**
```python
# Dry run to see what would be deleted
output = git.clean(dry_run=True)

# Actually clean
git.clean(directories=True)
```

### Submodule Operations

#### `submodule_add(url, path, branch=None)`
Add a submodule.

**Input:**
- `url` (str): Submodule repository URL
- `path` (str): Path where submodule will be placed
- `branch` (str, optional): Specific branch to track

**Output:**
- Returns `True` on success

**Example:**
```python
git.submodule_add("https://github.com/user/lib.git", "libs/mylib")
```

#### `submodule_init()`
Initialize submodules.

**Output:**
- Returns `True` on success

#### `submodule_update(init=False, recursive=False)`
Update submodules.

**Input:**
- `init` (bool): Initialize submodules
- `recursive` (bool): Update recursively

**Output:**
- Returns `True` on success

**Example:**
```python
git.submodule_update(init=True, recursive=True)
```

#### `submodule_list()`
List submodules.

**Output:**
- Returns list of submodule dictionaries

**Example:**
```python
submodules = git.submodule_list()
# [{'commit': 'abc123', 'path': 'libs/mylib', 'branch': 'main'}, ...]
```

### Advanced Operations

#### `blame(file, line_range=None)`
Show what revision and author last modified each line.

**Input:**
- `file` (str): File to blame
- `line_range` (tuple, optional): Tuple of (start_line, end_line)

**Output:**
- Returns blame output (str)

**Example:**
```python
blame = git.blame("src/main.py")
blame = git.blame("src/main.py", line_range=(10, 20))
```

#### `grep(pattern, files=None, ignore_case=False, line_number=False)`
Search for pattern in tracked files.

**Input:**
- `pattern` (str): Pattern to search for
- `files` (list, optional): Specific files to search
- `ignore_case` (bool): Case-insensitive search
- `line_number` (bool): Show line numbers

**Output:**
- Returns grep output (str)

**Example:**
```python
results = git.grep("TODO", ignore_case=True, line_number=True)
```

#### `archive(output_file, ref="HEAD", format="zip")`
Create archive of files from a tree.

**Input:**
- `output_file` (str): Output archive file
- `ref` (str): Tree reference (default: "HEAD")
- `format` (str): Archive format ("zip", "tar", "tar.gz")

**Output:**
- Returns `True` on success

**Example:**
```python
git.archive("release.zip", ref="v1.0.0")
git.archive("backup.tar.gz", format="tar.gz")
```

### Maintenance Operations

#### `gc(aggressive=False, prune=True)`
Cleanup unnecessary files and optimize repository.

**Input:**
- `aggressive` (bool): More aggressive optimization
- `prune` (bool): Prune loose objects

**Output:**
- Returns `True` on success

**Example:**
```python
git.gc()
git.gc(aggressive=True)
```

#### `fsck(full=False)`
Verify the connectivity and validity of objects.

**Input:**
- `full` (bool): Check all objects

**Output:**
- Returns fsck output (str)

**Example:**
```python
result = git.fsck(full=True)
```

#### `count_objects(verbose=True)`
Count unpacked objects and their disk consumption.

**Input:**
- `verbose` (bool): Show detailed information

**Output:**
- Returns dictionary with object statistics

**Example:**
```python
stats = git.count_objects()
# {'count': '42', 'size': '168', 'in-pack': '1234', ...}
```

### Utility Functions

#### `version()`
Get Git version.

**Output:**
- Returns Git version string

**Example:**
```python
version = git.version()
```

#### `get_repo_root()`
Get the root directory of the repository.

**Output:**
- Returns Path to repository root

**Example:**
```python
root = git.get_repo_root()
```

#### `is_inside_work_tree()`
Check if inside a Git work tree.

**Output:**
- Returns `True` if inside work tree

**Example:**
```python
if git.is_inside_work_tree():
    print("In a Git repository")
```

#### `has_uncommitted_changes()`
Check if there are uncommitted changes.

**Output:**
- Returns `True` if there are uncommitted changes

**Example:**
```python
if git.has_uncommitted_changes():
    print("You have uncommitted changes")
```

#### `get_contributors()`
Get list of contributors with commit counts.

**Output:**
- Returns list of contributor dictionaries

**Example:**
```python
contributors = git.get_contributors()
# [{'commits': 150, 'name': 'John Doe', 'email': 'john@example.com'}, ...]
```

#### `get_file_history(file, max_count=None)`
Get commit history for a specific file.

**Input:**
- `file` (str): File path
- `max_count` (int, optional): Maximum number of commits

**Output:**
- Returns list of commit dictionaries

**Example:**
```python
history = git.get_file_history("src/main.py", max_count=10)
```

## Complete Workflow Examples

### Feature Development Workflow

```python
from git_manager import GitManager

git = GitManager()

# Start new feature
git.checkout("develop")
git.pull()
git.branch_create("feature/user-authentication")
git.checkout("feature/user-authentication")

# Make changes
git.add_all()
git.commit("Implement user login")

# More changes
git.add(["auth.py", "tests/test_auth.py"])
git.commit("Add authentication tests")

# Push feature branch
git.push(remote="origin", branch="feature/user-authentication", 
         set_upstream=True)

# Merge back to develop
git.checkout("develop")
git.merge("feature/user-authentication", no_ff=True)
git.push()

# Clean up
git.branch_delete("feature/user-authentication")
```

### Release Management

```python
# Create release branch
git.checkout("develop")
git.branch_create("release/1.0.0")
git.checkout("release/1.0.0")

# Make release preparations
git.add("version.py")
git.commit("Bump version to 1.0.0")

# Merge to main and tag
git.checkout("main")
git.merge("release/1.0.0")
git.tag_create("v1.0.0", message="Release version 1.0.0")
git.push(tags=True)

# Merge back to develop
git.checkout("develop")
git.merge("release/1.0.0")
git.push()

# Archive release
git.archive("release-1.0.0.zip", ref="v1.0.0")
```

### Hotfix Workflow

```python
# Create hotfix branch from main
git.checkout("main")
git.branch_create("hotfix/critical-bug")
git.checkout("hotfix/critical-bug")

# Fix the bug
git.add("bug_file.py")
git.commit("Fix critical security vulnerability")

# Merge to main
git.checkout("main")
git.merge("hotfix/critical-bug")
git.tag_create("v1.0.1", message="Hotfix release 1.0.1")
git.push(tags=True)

# Merge to develop
git.checkout("develop")
git.merge("hotfix/critical-bug")
git.push()
```

### Repository Maintenance

```python
# Check repository health
print(f"Total commits: {git.get_commit_count()}")
print(f"Current branch: {git.get_current_branch()}")

# View statistics
stats = git.count_objects()
print(f"Repository size: {stats}")

# Clean up
git.gc(aggressive=True)
git.remote("prune", "origin")

# Verify integrity
print(git.fsck(full=True))

# Get contributors
for contributor in git.get_contributors():
    print(f"{contributor['name']}: {contributor['commits']} commits")
```

## Error Handling

The GitManager includes comprehensive error handling:

```python
from git_manager import GitManager
import logging

try:
    git = GitManager(repo_path="/path/to/repo", log_level=logging.DEBUG)
    git.commit("My commit message")
except subprocess.CalledProcessError as e:
    print(f"Git command failed: {e}")
except EnvironmentError as e:
    print(f"Environment error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Always check status before operations:**
   ```python
   if git.has_uncommitted_changes():
       print("Commit or stash your changes first")
   ```

2. **Use dry-run when available:**
   ```python
   # Check what will be cleaned
   git.clean(dry_run=True)
   ```

3. **Verify merge/rebase state:**
   ```python
   if git.is_merge_in_progress():
       git.merge_abort()
   ```

4. **Enable logging for debugging:**
   ```python
   git = GitManager(log_level=logging.DEBUG)
   ```

5. **Handle conflicts gracefully:**
   ```python
   try:
       git.merge("feature-branch")
   except subprocess.CalledProcessError:
       print("Merge conflict! Resolve manually")
       # After resolving:
       git.add_all()
       git.commit("Merge feature-branch")
   ```

## License

MIT License - Feel free to use in your enterprise projects.

## Contributing

Contributions welcome! Please ensure:
- Type hints for all function parameters and returns
- Docstrings for all public methods
- Unit tests for new functionality
- Logging for important operations

## Support

For issues and questions:
- Check the API reference above
- Review the examples
- Enable DEBUG logging for troubleshooting