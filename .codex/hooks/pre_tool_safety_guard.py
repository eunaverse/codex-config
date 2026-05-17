#!/usr/bin/env python3
"""Block high-risk shell actions before Codex tool execution."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


SHELL_READ_COMMANDS = {
    "awk",
    "bat",
    "cat",
    "grep",
    "head",
    "less",
    "more",
    "nl",
    "rg",
    "sed",
    "tail",
}

SENSITIVE_ENV_VARS = {
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "OPENAI_API_KEY",
    "SLACK_BOT_TOKEN",
    "SLACK_WEBHOOK_URL",
}

SENSITIVE_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env(\..*)?$"),
    re.compile(r"(^|/)auth\.json$"),
    re.compile(r"(^|/)credentials$"),
    re.compile(r"(^|/)\.aws/(credentials|config)$"),
    re.compile(r"(^|/)\.ssh/(id_rsa|id_dsa|id_ecdsa|id_ed25519)(\.pub)?$"),
    re.compile(r"(^|/)(secrets?|secret|token|tokens)(\..*)?$", re.IGNORECASE),
    re.compile(r".*\.(pem|key|p12|pfx|p8)$", re.IGNORECASE),
    re.compile(r".*service[-_]?account.*\.json$", re.IGNORECASE),
)


def main() -> int:
    payload = read_payload()
    command = get_command(payload)
    if not command:
        return 0

    workdir = get_workdir(payload)
    reason = check_command(command, workdir)
    if reason:
        deny(reason)
    return 0


def read_payload() -> dict:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def get_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("cmd") or tool_input.get("command")
    return command if isinstance(command, str) else ""


def get_workdir(payload: dict) -> Path:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        workdir = tool_input.get("workdir")
        if isinstance(workdir, str) and workdir:
            return Path(workdir).expanduser()
    return Path.cwd()


def check_command(command: str, workdir: Path) -> str | None:
    try:
        tokens = shell_tokens(command)
        segments = command_segments(tokens)
    except ValueError:
        return regex_fallback_check(command)

    for segment in segments:
        reason = check_segment(segment, workdir)
        if reason:
            return reason
    return None


def shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|(){}\n")
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"
    return list(lexer)


def command_segments(tokens: Iterable[str]) -> list[list[str]]:
    separators = {";", "&", "&&", "|", "|&", "||", "(", ")", "{", "}", "\n"}
    segments: list[list[str]] = []
    current: list[str] = []

    for token in tokens:
        if token in separators:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)

    if current:
        segments.append(current)
    return segments


def check_segment(tokens: list[str], workdir: Path) -> str | None:
    executable_index = first_executable_index(tokens)
    if executable_index is None:
        return None

    executable = basename(tokens[executable_index])
    args = tokens[executable_index + 1 :]

    if executable in {"sh", "bash", "zsh"}:
        nested = shell_command_argument(args)
        return check_command(nested, workdir) if nested else None

    destructive = check_destructive(executable, args)
    if destructive:
        return destructive

    secret = check_secret_exposure(executable, args, workdir)
    if secret:
        return secret

    return None


def first_executable_index(tokens: list[str]) -> int | None:
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if is_env_assignment(token):
            i += 1
            continue
        if basename(token) == "sudo":
            i = skip_sudo_options(tokens, i + 1)
            continue
        if basename(token) in {"command", "exec", "nohup", "time"}:
            i = skip_simple_wrapper_options(tokens, i + 1)
            continue
        if basename(token) == "env":
            next_index = env_wrapped_command_index(tokens, i + 1)
            if next_index is None:
                return i
            i = next_index
            continue
        return i
    return None


def is_env_assignment(token: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token))


def basename(token: str) -> str:
    return Path(token).name


def skip_sudo_options(tokens: list[str], start: int) -> int:
    i = start
    options_with_value = {"-C", "-D", "-g", "-h", "-p", "-R", "-r", "-t", "-T", "-u"}
    while i < len(tokens) and tokens[i].startswith("-"):
        option = tokens[i]
        if option == "--":
            return i + 1
        if option in options_with_value and i + 1 < len(tokens):
            i += 2
        else:
            i += 1
    return i


def skip_simple_wrapper_options(tokens: list[str], start: int) -> int:
    i = start
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i] == "--":
            return i + 1
        i += 1
    return i


def env_wrapped_command_index(tokens: list[str], start: int) -> int | None:
    i = start
    while i < len(tokens):
        token = tokens[i]
        if is_env_assignment(token):
            i += 1
            continue
        if token == "--":
            return i + 1 if i + 1 < len(tokens) else None
        if token in {"-i", "-0", "-v", "--ignore-environment", "--null", "--debug"}:
            i += 1
            continue
        if token in {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"}:
            i += 2
            continue
        if token.startswith(("--unset=", "--chdir=", "--split-string=")):
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        return i
    return None


def shell_command_argument(args: list[str]) -> str:
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-c" and i + 1 < len(args):
            return args[i + 1]
        i += 1
    return ""


def check_destructive(executable: str, args: list[str]) -> str | None:
    if executable == "rm" and has_short_or_long_flag(args, "r", "recursive") and has_short_or_long_flag(args, "f", "force"):
        return "Blocking destructive command: `rm -rf` style recursive forced deletion requires an explicit manual path."

    if executable in {"chmod", "chown"} and has_short_or_long_flag(args, "R", "recursive"):
        return f"Blocking destructive command: `{executable} -R` can broadly mutate permissions/ownership."

    if executable == "git":
        git_reason = check_destructive_git(args)
        if git_reason:
            return git_reason

    if executable == "find" and "-delete" in args:
        return "Blocking destructive command: `find ... -delete` can remove many files unexpectedly."

    return None


def check_destructive_git(args: list[str]) -> str | None:
    git_args = strip_git_global_options(args)
    if len(git_args) >= 2 and git_args[0] == "reset" and "--hard" in git_args[1:]:
        return "Blocking destructive command: `git reset --hard` would discard local changes."
    if len(git_args) >= 2 and git_args[0] == "checkout" and "--" in git_args[1:]:
        return "Blocking destructive command: `git checkout -- <path>` would overwrite local files."
    if git_args and git_args[0] == "clean":
        joined = " ".join(git_args[1:])
        if re.search(r"(^|\s)-[A-Za-z]*f[A-Za-z]*d|(^|\s)-[A-Za-z]*d[A-Za-z]*f", joined):
            return "Blocking destructive command: `git clean -fd` would delete untracked files."
        if "--force" in git_args and any(arg in {"-d", "--directories"} for arg in git_args):
            return "Blocking destructive command: `git clean --force -d` would delete untracked files."
    return None


def strip_git_global_options(args: list[str]) -> list[str]:
    result = list(args)
    while result:
        arg = result[0]
        if arg == "-C" and len(result) >= 2:
            result = result[2:]
        elif arg in {"-c", "--git-dir", "--work-tree", "--namespace"} and len(result) >= 2:
            result = result[2:]
        elif arg.startswith(("-c=", "--git-dir=", "--work-tree=", "--namespace=")):
            result = result[1:]
        else:
            break
    return result


def has_short_or_long_flag(args: list[str], short: str, long: str) -> bool:
    for arg in args:
        if arg == f"--{long}" or arg.startswith(f"--{long}="):
            return True
        if arg.startswith("-") and not arg.startswith("--") and short in arg[1:]:
            return True
    return False


def check_secret_exposure(executable: str, args: list[str], workdir: Path) -> str | None:
    if executable in {"env", "printenv"} and would_print_environment(executable, args):
        return "Blocking environment dump because it may expose API keys or credentials."

    if executable in {"echo", "printf"} and references_sensitive_env(" ".join(args)):
        return "Blocking command that prints a sensitive environment variable."

    if executable in SHELL_READ_COMMANDS:
        sensitive = first_sensitive_path(args, workdir)
        if sensitive:
            return f"Blocking read of sensitive file path: `{sensitive}`."

    if executable == "git":
        sensitive = check_git_add_secret(args, workdir)
        if sensitive:
            return sensitive

    return None


def would_print_environment(executable: str, args: list[str]) -> bool:
    non_option_args = [arg for arg in args if not arg.startswith("-")]
    if executable == "env":
        wrapped = env_wrapped_command_index([executable, *args], 1)
        return wrapped is None
    if executable == "printenv":
        return not non_option_args or any(arg in SENSITIVE_ENV_VARS for arg in non_option_args)
    return False


def references_sensitive_env(text: str) -> bool:
    return any(re.search(rf"\$\{{?{re.escape(name)}\}}?", text) for name in SENSITIVE_ENV_VARS)


def first_sensitive_path(args: list[str], workdir: Path) -> str:
    for arg in path_like_args(args):
        normalized = normalize_path(arg, workdir)
        if is_sensitive_path(normalized):
            return arg
    return ""


def path_like_args(args: Iterable[str]) -> Iterable[str]:
    skip_next_for = {
        "-A",
        "-B",
        "-C",
        "-e",
        "-f",
        "-m",
        "-n",
        "-o",
        "-r",
        "-s",
        "-t",
        "--after-context",
        "--before-context",
        "--context",
        "--file",
        "--max-count",
        "--regexp",
    }
    iterator = iter(args)
    for arg in iterator:
        if arg == "--":
            yield from iterator
            return
        if arg in skip_next_for:
            next(iterator, None)
            continue
        if arg.startswith("-"):
            continue
        if re.search(r"(^|/)\.?[A-Za-z0-9_.-]+", arg):
            yield arg


def normalize_path(path_text: str, workdir: Path) -> str:
    expanded = os.path.expandvars(os.path.expanduser(path_text))
    path = Path(expanded)
    if not path.is_absolute():
        path = workdir / path
    try:
        return str(path.resolve(strict=False))
    except Exception:
        return str(path)


def is_sensitive_path(path_text: str) -> bool:
    return any(pattern.search(path_text) for pattern in SENSITIVE_PATH_PATTERNS)


def check_git_add_secret(args: list[str], workdir: Path) -> str | None:
    git_args = strip_git_global_options(args)
    if not git_args or git_args[0] != "add":
        return None

    add_args = git_args[1:]
    explicit_sensitive = first_sensitive_path(add_args, workdir)
    if explicit_sensitive:
        return f"Blocking `git add` of sensitive file path: `{explicit_sensitive}`."

    if any(arg in {"-A", "--all", "."} for arg in add_args):
        sensitive_status = sensitive_git_status_path(workdir)
        if sensitive_status:
            return f"Blocking broad `git add` because sensitive file is present in git status: `{sensitive_status}`."

    return None


def sensitive_git_status_path(workdir: Path) -> str:
    result = subprocess.run(
        ("git", "status", "--porcelain", "-z"),
        cwd=workdir,
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return ""
    entries = result.stdout.split(b"\0")
    for entry in entries:
        if not entry:
            continue
        text = entry.decode(errors="replace")
        path = text[3:] if len(text) > 3 else text
        path = path.split(" -> ", 1)[-1]
        normalized = normalize_path(path, workdir)
        if is_sensitive_path(normalized):
            return path
    return ""


def regex_fallback_check(command: str) -> str | None:
    if re.search(r"(^|[;&|()])\s*rm\s+[^;&|]*-[A-Za-z]*r[A-Za-z]*f|(^|[;&|()])\s*rm\s+[^;&|]*-[A-Za-z]*f[A-Za-z]*r", command):
        return "Blocking destructive command: `rm -rf` style recursive forced deletion requires an explicit manual path."
    if re.search(r"(^|[;&|()])\s*git\s+reset\s+--hard(\s|$)", command):
        return "Blocking destructive command: `git reset --hard` would discard local changes."
    if re.search(r"(^|[;&|()])\s*git\s+checkout\s+--(\s|$)", command):
        return "Blocking destructive command: `git checkout -- <path>` would overwrite local files."
    if references_sensitive_env(command):
        return "Blocking command that references a sensitive environment variable."
    return None


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
