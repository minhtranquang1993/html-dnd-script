#!/usr/bin/env python3
"""
git_push_helper.py — Bridge module between push scripts and TokenManager.

Provides:
- get_token_for_repo(): auto-select token via TokenManager
- git_push(): commit + push with transient auth (no token persisted in remote URL)

Used by:
- skills/seo-outline/scripts/push_to_github.py
- skills/seo-article/scripts/push_to_github.py
"""

import base64
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add tools/ to sys.path for github_token_manager import
_HELPER_DIR = Path(__file__).resolve().parent
_TOOLS_DIR = _HELPER_DIR / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from github_token_manager import (
    TokenConfig,
    TokenEntry,
    select_token,
    mask_token,
)

logger = logging.getLogger("git-push-helper")

# Default config path
DEFAULT_TOKEN_CONFIG = _HELPER_DIR / "credentials" / "token_config.json"


def _resolve_file_tokens(config: TokenConfig) -> None:
    """Read token values from file_path fields if value is not already set."""
    for entry in config.tokens:
        if entry.value:
            continue
        if entry.file_path:
            token_file = Path(entry.file_path)
            # Support relative paths from workspace root
            if not token_file.is_absolute():
                token_file = _HELPER_DIR / token_file
            if token_file.exists():
                raw = token_file.read_text(encoding="utf-8").strip()
                if raw:
                    entry.value = raw
                    logger.debug("Loaded token '%s' from file %s", entry.alias, token_file.name)


def get_token_for_repo(repo: str, config_path: Path | None = None) -> str | None:
    """Auto-select the best GitHub token for a given repo.

    Args:
        repo: Repository in "owner/repo" format.
        config_path: Path to token_config.json (default: credentials/token_config.json).

    Returns:
        Token string if found, None otherwise.
    """
    config_path = config_path or DEFAULT_TOKEN_CONFIG
    config = TokenConfig.from_json(config_path)

    # Resolve file-based tokens
    _resolve_file_tokens(config)

    result = select_token(config, repo, verbose=True)

    if result.success:
        logger.info("Token selected: %s (%s)", result.alias, mask_token(result.token))
        return result.token
    else:
        logger.error("All tokens failed for %s: %s", repo, result.message)
        return None


def git_push(
    repo: str,
    repo_dir: str = ".",
    branch: str = "main",
    commit_msg: str = "update",
    verbose: bool = False,
) -> bool:
    """Commit and push to GitHub using auto-selected token.

    Auth is transient (via git credential helper env) — token is NOT persisted
    in remote URL.

    Args:
        repo: Repository in "owner/repo" format.
        repo_dir: Local git repo directory.
        branch: Branch to push to.
        commit_msg: Commit message.
        verbose: Print detailed logs.

    Returns:
        True if push succeeded (or nothing to push).
    """
    token = get_token_for_repo(repo)
    if not token:
        logger.error("No valid token available — aborting push")
        return False

    repo_path = Path(repo_dir).resolve()

    def _run(cmd: list[str], extra_env: dict | None = None, **kwargs) -> subprocess.CompletedProcess:
        """Run a git command in the repo directory."""
        env = None
        if extra_env:
            env = {**os.environ, **extra_env}
        return subprocess.run(
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            **kwargs,
        )

    # Check for uncommitted changes and stage+commit if any
    status_result = _run(["git", "status", "--porcelain"])
    if status_result.returncode != 0:
        logger.error("git status failed: %s", status_result.stderr)
        return False

    has_changes = bool(status_result.stdout.strip())

    if has_changes:
        # Stage all changes
        add_result = _run(["git", "add", "-A"])
        if add_result.returncode != 0:
            logger.error("git add failed: %s", add_result.stderr)
            return False

        # Commit
        commit_result = _run(["git", "commit", "-m", commit_msg])
        if commit_result.returncode != 0:
            if "nothing to commit" in commit_result.stdout:
                logger.info("Nothing to commit — already up to date")
            else:
                logger.error("git commit failed: %s", commit_result.stderr)
                return False

        if verbose:
            logger.info("Committed: %s", commit_result.stdout.strip().split("\n")[0])
    else:
        logger.info("No uncommitted changes — will push existing commits if any")

    # Push with transient auth via environment variable (not CLI args, to avoid
    # token exposure in process listings)
    remote_url = f"https://github.com/{repo}.git"
    auth_header = f"Authorization: Basic {_encode_token(token)}"

    push_result = _run(
        ["git", "push", remote_url, branch],
        extra_env={"GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "http.extraHeader",
                    "GIT_CONFIG_VALUE_0": auth_header},
    )

    if push_result.returncode != 0:
        logger.error("git push failed: %s", push_result.stderr)
        return False

    masked = mask_token(token)
    logger.info("Pushed to %s (branch: %s) with token %s", repo, branch, masked)
    return True


def _encode_token(token: str) -> str:
    """Encode token for HTTP Basic auth (username:password base64)."""
    # GitHub accepts token as password with 'x-access-token' as username
    credentials = f"x-access-token:{token}"
    return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
