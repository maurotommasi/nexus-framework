import os
from typing import Optional
from pathlib import Path
from datetime import datetime
from framework.core.security import Security

class CLIUtils:
    """Collection of CLI utility functions."""

    LOG_DIR = "logs"

    def __init__(self, root_path: str, security: Security):
        self.root_path = Path(root_path)
        self.security = security
        (self.root_path / self.LOG_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_tree(start_path: str, prefix: str = "") -> str:
        """
        Recursively builds a directory tree as a string starting at `start_path`.

        Args:
            start_path (str): Path to the root directory.
            prefix (str): Internal use for recursive indentation.

        Returns:
            str: Directory tree as a string.
        """
        lines = []
        items = sorted(os.listdir(start_path))
        for index, item in enumerate(items):
            path = os.path.join(start_path, item)
            connector = "└── " if index == len(items) - 1 else "├── "
            lines.append(prefix + connector + item)
            if os.path.isdir(path):
                extension = "    " if index == len(items) - 1 else "│   "
                lines.append(CLIUtils.get_tree(path, prefix + extension))
        return "\n".join(lines)

    def _get_log_file_path(self) -> Path:
        """Return daily log file path."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.root_path / self.LOG_DIR / f"nexus-{date_str}.log"

    def print(self, text: str, save_log: bool = False, encrypt_log: bool = False) -> None:
        """
        Prints text to CLI and appends encrypted text to log file.
        """
        # Print to CLI
        print(text)

        # Encrypt text
        if encrypt_log: encrypted_data = self.security.encrypt(text)
        else: encrypted_data = text.encode("utf-8")
        if save_log:
            # Ensure log directory exists
            (self.root_path / self.LOG_DIR).mkdir(parents=True, exist_ok=True)

            # Append encrypted data to daily log file
            log_file = self._get_log_file_path()
            with open(log_file, "ab") as f:
                # Add newline separator
                f.write(encrypted_data + b"\n")