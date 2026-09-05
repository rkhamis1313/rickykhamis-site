#!/usr/bin/env python3
"""Gated publish: screen, render, verify, commit, push, then prove the push landed.

Every step is checked. The first failure stops the run and prints a single line
beginning with "PUBLISH FAILED:" naming the step and the reason, so the caller
has something exact to put in an alert instead of a generic "it broke".

Exit codes:
    0  published and the push was confirmed on the remote, or nothing to do
    1  a step failed (details on stdout, last line is the PUBLISH FAILED line)

Usage:
    python gen/publish.py
    python gen/publish.py --dry-run     # everything except commit and push
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANCH = "claude/rickykhamis-daily-blog-automation-dovt88"


class StepFailed(Exception):
    def __init__(self, step: str, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.step = step
        self.reason = reason
        self.detail = detail.strip()


def run(cmd: list[str], step: str, expect_zero: bool = True) -> str:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    print(output.rstrip(), flush=True)
    if expect_zero and proc.returncode != 0:
        raise StepFailed(
            step,
            f"`{' '.join(cmd)}` exited {proc.returncode}",
            output[-1500:],
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        posts = sorted((ROOT / "content" / "posts").glob("*.md"))
        if not posts:
            raise StepFailed("screen", "no markdown posts found in content/posts/")

        # 1. House style and advertising compliance, before anything is rendered.
        run(["python3", "gen/compliance_check.py",
             *[str(p.relative_to(ROOT)) for p in posts]],
            "compliance_check")

        # 2. Render. new_post.py runs its own --check and exits non-zero on a
        #    failed consistency pass.
        render = run(["python3", "gen/new_post.py", "--all-unpublished"], "render")
        if "All consistent." not in render:
            raise StepFailed("render", "new_post.py did not report 'All consistent.'",
                             render[-1500:])

        # 3. Independent consistency pass, so a bad render cannot reach the site
        #    even if step 2 somehow returned zero.
        check = run(["python3", "gen/new_post.py", "--check"], "verify")
        if "All consistent." not in check:
            raise StepFailed("verify", "site is not internally consistent",
                             check[-1500:])

        # 4. Stage. Nothing staged is a legitimate no-op, not a failure.
        run(["git", "add", "-A"], "stage")
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
        if staged.returncode == 0:
            print("\nNothing to publish; working tree already matches the site.")
            return 0

        if args.dry_run:
            print("\n--dry-run: stopping before commit and push.")
            return 0

        # 5. Commit.
        message = f"Publish daily posts ({date.today().isoformat()})"
        run(["git", "-c", "user.name=github-actions[bot]",
             "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
             "commit", "-m", message], "commit")

        local = run(["git", "rev-parse", "HEAD"], "commit").strip().splitlines()[-1]

        # 6. Push.
        run(["git", "push", "origin", f"HEAD:{BRANCH}"], "push")

        # 7. Prove it landed. A push that reports success but leaves the remote
        #    behind is the failure mode worth catching, since Netlify deploys
        #    from the remote, not from here.
        remote_out = run(["git", "ls-remote", "origin", f"refs/heads/{BRANCH}"],
                         "confirm-push")
        remote = ""
        for line in remote_out.splitlines():
            if line.strip().endswith(f"refs/heads/{BRANCH}"):
                remote = line.split()[0]
                break
        if not remote:
            raise StepFailed("confirm-push",
                             f"branch {BRANCH} not found on origin after push")
        if remote != local:
            raise StepFailed(
                "confirm-push",
                f"remote is {remote[:8]} but local HEAD is {local[:8]}; "
                "the push did not land",
            )

        print(f"\nPublished and confirmed on origin at {local[:8]}.")
        return 0

    except StepFailed as failure:
        if failure.detail:
            print(f"\n--- detail ---\n{failure.detail}", flush=True)
        print(f"\nPUBLISH FAILED: step={failure.step}: {failure.reason}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
