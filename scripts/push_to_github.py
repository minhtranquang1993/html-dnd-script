#!/usr/bin/env python3
"""
push_to_github.py — Push DND HTML content to GitHub using TokenManager.

Writes HTML content to a file in a cloned repo, commits, and pushes.
Returns the GitHub blob URL for the pushed file.

Usage:
    python3 push_to_github.py --slug keyword-slug --html '<article>...</article>'
    python3 push_to_github.py --slug keyword-slug --html-file /tmp/content.html
    python3 push_to_github.py --slug keyword-slug --html '<article>...' --branch main -v
"""

import argparse
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

# Add workspace root to path so we can import git_push_helper
_SCRIPT_DIR = Path(__file__).resolve().parent
_WORKSPACE = _SCRIPT_DIR.parents[2]  # skills/dnd-html/scripts -> dnd-html -> skills -> workspace
if str(_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE))

from git_push_helper import get_token_for_repo

logger = logging.getLogger("dnd-html.push")

REPO = "minhtranquang1993/dnd-html-content"
BRANCH = "main"
GIT_NAME = "Minh Tran"
GIT_EMAIL = "minhtqm131293@gmail.com"


def clone_repo(token: str, repo: str, branch: str, dest: Path) -> bool:
    """Clone repo with token auth into dest directory."""
    remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    result = subprocess.run(
        ["git", "clone", "--depth=1", "--branch", branch, remote_url, str(dest)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        logger.error("git clone failed: %s", result.stderr)
        return False
    return True


def push_html(slug: str, html_content: str, branch: str = BRANCH, verbose: bool = False):
    """
    Clone dnd-html-content repo, write HTML file, commit & push.

    Returns:
        GitHub blob URL of the pushed file, or None on failure.
    """
    token = get_token_for_repo(REPO)
    if not token:
        logger.error("No valid GitHub token -- aborting")
        return None

    with tempfile.TemporaryDirectory(prefix="dnd-html-push-") as tmpdir:
        repo_path = Path(tmpdir) / "repo"

        logger.info("Cloning %s ...", REPO)
        if not clone_repo(token, REPO, branch, repo_path):
            return None

        # Configure git identity in the cloned repo
        subprocess.run(["git", "config", "user.name", GIT_NAME],
                       cwd=str(repo_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", GIT_EMAIL],
                       cwd=str(repo_path), check=True, capture_output=True)

        # Write HTML file
        filename = f"{slug}.html"
        file_path = repo_path / filename
        file_path.write_text(html_content, encoding="utf-8")
        logger.info("Wrote %s (%d bytes)", filename, len(html_content))

        # Stage
        result = subprocess.run(
            ["git", "add", filename],
            cwd=str(repo_path), capture_output=True, text=True,
        )
        if result.returncode != 0:
            logger.error("git add failed: %s", result.stderr)
            return None

        # Check if there is actually something to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_path), capture_output=True, text=True,
        )
        if not status.stdout.strip():
            logger.info("No changes to commit -- file already identical")
        else:
            commit_msg = f"add: {slug}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(repo_path), capture_output=True, text=True,
            )
            if result.returncode != 0:
                logger.error("git commit failed: %s", result.stderr)
                return None
            if verbose:
                logger.info("Committed: %s", result.stdout.strip().split("\n")[0])

        # Push with token in remote URL (temp dir, token never persisted)
        remote_url = f"https://x-access-token:{token}@github.com/{REPO}.git"
        result = subprocess.run(
            ["git", "push", remote_url, branch],
            cwd=str(repo_path), capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            logger.error("git push failed: %s", result.stderr)
            return None

        github_url = f"https://github.com/{REPO}/blob/{branch}/{filename}"
        logger.info("Pushed: %s", github_url)
        return github_url


def main():
    parser = argparse.ArgumentParser(
        description="Push DND HTML article to GitHub dnd-html-content repo",
    )
    parser.add_argument("--slug", required=True, help="Keyword slug (filename without .html)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--html", help="HTML content string")
    group.add_argument("--html-file", help="Path to file containing HTML content")
    parser.add_argument("--branch", default=BRANCH, help=f"Branch (default: {BRANCH})")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.html_file:
        html_content = Path(args.html_file).read_text(encoding="utf-8")
    else:
        html_content = args.html

    url = push_html(args.slug, html_content, branch=args.branch, verbose=args.verbose)

    if url:
        print(url)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
