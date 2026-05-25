"""Sandbox runner: executes a user's Linux command inside an isolated Docker
container and returns the result. This is the security boundary of the game —
no user input ever touches the host shell.

Each command gets a fresh container. The container has no network, runs as a
non-root user, and is hard-killed after SANDBOX_TIMEOUT seconds.

Originally missing from the project entirely. Added during revival because
without this the game cannot actually grade anything.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "linux-mastery-sandbox")
SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "10"))


@dataclass
class SandboxResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
        }


def run_in_sandbox(command: str, setup_script: str | None = None) -> SandboxResult:
    """Run a single user command inside a one-shot Docker container.

    Args:
        command: The user-supplied Linux command (passed to `sh -c`).
        setup_script: Optional bash snippet to run BEFORE the user command,
            used by scenarios to seed the container state (e.g. fill a
            filesystem, start a fake service). Trusted scenario content only.
    """
    if not command or not command.strip():
        return SandboxResult(command, "", "empty command", 1, False)

    if setup_script:
        full_command = f"{setup_script}\nset +e\n{command}"
    else:
        full_command = command

    # docker run --rm --network=none --memory=256m --cpus=0.5 \
    #   --user 1000:1000 IMAGE sh -c '...'
    docker_args = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--memory=256m",
        "--cpus=0.5",
        "--user", "1000:1000",
        SANDBOX_IMAGE,
        "sh", "-c", full_command,
    ]

    try:
        proc = subprocess.run(
            docker_args,
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
        )
        return SandboxResult(
            command=command,
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(
            command=command,
            stdout="",
            stderr=f"Command exceeded {SANDBOX_TIMEOUT}s timeout and was killed.",
            exit_code=124,
            timed_out=True,
        )
    except FileNotFoundError:
        return SandboxResult(
            command=command,
            stdout="",
            stderr=(
                "Docker not found on PATH. Install Docker Desktop and ensure "
                "the daemon is running, then `docker build -t "
                f"{SANDBOX_IMAGE} sandbox/`."
            ),
            exit_code=127,
            timed_out=False,
        )


def sandbox_image_exists() -> bool:
    """Quick health check used by /mission/start to give clearer errors."""
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", SANDBOX_IMAGE],
            capture_output=True,
            timeout=5,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
