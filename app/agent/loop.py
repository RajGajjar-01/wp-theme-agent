import json
import os
import logging
import time
import traceback
from pathlib import Path
from typing import Callable, Any

import httpx
import httpcore
from openai import OpenAI
from dotenv import load_dotenv
from app.agent.tools import (
    write_file,
    read_file,
    list_files,
    run_php_lint,
    copy_file,
    copy_section,
    search_in_file,
    grep_workspace,
    list_base_theme_files,
    read_base_theme_file,
    seed_workspace_with_base_theme,
)
from app.agent.prompts.system_prompt import build_system_prompt

load_dotenv()

logger = logging.getLogger("agent")

client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url="https://api.fireworks.ai/inference/v1",
    timeout=httpx.Timeout(
        connect=60.0,  # 60s to establish connection
        read=300.0,  # 300s max between data chunks during streaming
        write=60.0,  # 60s for sending request
        pool=60.0,  # 60s to acquire connection from pool
    ),
)

MODEL = "accounts/fireworks/models/glm-5"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the theme output folder. Use for creating or modifying files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to workspace (e.g., 'output/header.php')",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file. Use 'uploads/filename' for uploaded source files, 'output/filename' for theme files you've created or modified.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (e.g., 'uploads/index.html' or 'output/style.css')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in the workspace (uploads + output) with sizes.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file directly without outputting its content. Saves tokens. Source can be 'base_theme/...', 'uploads/...', or 'output/...'. Destination is always relative to workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Source file path (e.g., 'base_theme/sidebar.php', 'uploads/logo.png')",
                    },
                    "dest": {
                        "type": "string",
                        "description": "Destination path (e.g., 'output/sidebar.php', 'output/assets/images/logo.png')",
                    },
                },
                "required": ["src", "dest"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_section",
            "description": "Extract a section between two regex patterns from a source file and write/append to a destination. Works for CSS, JS, HTML, PHP. Great for copying specific CSS blocks, JS functions, or HTML sections without regenerating them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src_file": {
                        "type": "string",
                        "description": "Source file path (supports 'base_theme/', 'uploads/', 'output/')",
                    },
                    "dest_file": {
                        "type": "string",
                        "description": "Destination file path",
                    },
                    "start_pattern": {
                        "type": "string",
                        "description": "Regex pattern marking the start of the section to extract",
                    },
                    "end_pattern": {
                        "type": "string",
                        "description": "Regex pattern marking the end of the section to extract",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["append", "overwrite"],
                        "description": "Whether to append to or overwrite the destination file. Default: append",
                    },
                },
                "required": ["src_file", "dest_file", "start_pattern", "end_pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search for a regex pattern in a single file. Returns matching lines with line numbers. Path supports 'base_theme/', 'uploads/', 'output/' prefixes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File to search in (e.g., 'base_theme/functions.php', 'uploads/styles.css')",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for (e.g., 'wp_nav_menu', '\\.hero', 'function.*setup')",
                    },
                },
                "required": ["path", "pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_workspace",
            "description": "Search across ALL workspace files for a regex pattern. Returns matching files and lines. Useful for finding where a CSS class, function, or HTML element is used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "file_glob": {
                        "type": "string",
                        "description": "Optional glob filter (e.g., '*.php', '*.css', '*.html'). Default: all files.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_base_theme_files",
            "description": "List all files in the original _s base theme with sizes. Use to see what's available to copy or reference.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_base_theme_file",
            "description": "Read a file from the _s base theme. Use to understand the base structure before modifying.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path within base theme (e.g., 'header.php', 'inc/template-tags.php')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_php_lint",
            "description": "Check a PHP file for syntax errors. Call after every .php file you write or modify.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to PHP file (e.g., 'output/header.php')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Call when ALL files have been written, modified, and linted. Stops the agent loop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of all files created/modified and what they do",
                    }
                },
                "required": ["summary"],
            },
        },
    },
]


def dispatch_tool(name: str, args: dict, workspace: Path, emit: Callable) -> str:
    """Execute a tool call and return the JSON result string."""
    logger.info(f"Tool call: {name} | args keys: {list(args.keys())}")
    emit("agent", "running", f"Calling {name}({list(args.keys())})")

    try:
        if name == "write_file":
            path = args.get("path", "")
            content = args.get("content", "")
            if not content:
                logger.warning(f"write_file called with empty content for {path}")
                return json.dumps(
                    {
                        "ok": False,
                        "error": "Content was empty (likely truncated). Please try writing a shorter version of the file.",
                    }
                )
            result = write_file(path, content, workspace)
            if result.get("ok"):
                logger.info(f"  ✓ Wrote {path} ({result.get('size', 0)} chars)")
                emit(
                    "agent", "complete", f"Wrote {path} ({result.get('size', 0)} chars)"
                )

        elif name == "read_file":
            result = read_file(args.get("path", ""), workspace)
            if result.get("ok"):
                logger.info(
                    f"  ✓ Read {args.get('path')} ({result.get('size', 0)} chars)"
                )

        elif name == "list_files":
            result = list_files(workspace)

        elif name == "copy_file":
            result = copy_file(args.get("src", ""), args.get("dest", ""), workspace)
            if result.get("ok"):
                logger.info(
                    f"  ✓ Copied {args.get('src')} → {args.get('dest')} ({result.get('size', 0)} bytes)"
                )
                emit(
                    "agent",
                    "complete",
                    f"Copied {args.get('src')} → {args.get('dest')}",
                )

        elif name == "copy_section":
            result = copy_section(
                src_file=args.get("src_file", ""),
                dest_file=args.get("dest_file", ""),
                start_pattern=args.get("start_pattern", ""),
                end_pattern=args.get("end_pattern", ""),
                workspace=workspace,
                mode=args.get("mode", "append"),
            )
            if result.get("ok"):
                logger.info(
                    f"  ✓ Copied section ({result.get('section_size', 0)} chars) → {args.get('dest_file')}"
                )
                emit(
                    "agent",
                    "complete",
                    f"Copied section to {args.get('dest_file')} ({result.get('section_size', 0)} chars)",
                )

        elif name == "search_in_file":
            result = search_in_file(
                args.get("path", ""), args.get("pattern", ""), workspace
            )
            if result.get("ok"):
                logger.info(
                    f"  ✓ Search '{args.get('pattern')}' in {args.get('path')}: {result.get('match_count', 0)} matches"
                )

        elif name == "grep_workspace":
            result = grep_workspace(
                pattern=args.get("pattern", ""),
                workspace=workspace,
                file_glob=args.get("file_glob", "*"),
            )
            if result.get("ok"):
                logger.info(
                    f"  ✓ Grep '{args.get('pattern')}': {result.get('total_matches', 0)} matches in {result.get('files_matched', 0)} files"
                )

        elif name == "list_base_theme_files":
            result = list_base_theme_files()

        elif name == "read_base_theme_file":
            result = read_base_theme_file(args.get("path", ""))
            if result.get("ok"):
                logger.info(
                    f"  ✓ Read base theme {args.get('path')} ({result.get('size', 0)} chars)"
                )

        elif name == "run_php_lint":
            result = run_php_lint(args.get("path", ""), workspace)
            if result.get("ok"):
                emit("agent", "complete", f"{args.get('path')} — no syntax errors")
            else:
                emit(
                    "agent",
                    "warning",
                    f"{args.get('path')} — lint error: {result.get('error', '')[:80]}",
                )

        elif name == "task_complete":
            result = {"ok": True, "done": True, "summary": args.get("summary", "")}
            emit("agent", "complete", args.get("summary", "Task complete"))

        else:
            result = {"ok": False, "error": f"Unknown tool: {name}"}

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        result = {"ok": False, "error": str(e)}

    return json.dumps(result)


# Transient network errors that should be retried
_RETRYABLE_EXCEPTIONS = (
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.PoolTimeout,
    httpcore.ReadError,
    httpcore.ReadTimeout,
    httpcore.RemoteProtocolError,
    ConnectionError,
    ConnectionResetError,
    TimeoutError,
)

# Max seconds to wait between stream chunks before considering the stream stalled
STREAM_CHUNK_TIMEOUT = 90

MAX_STREAM_RETRIES = 3


def _stream_and_collect(messages, emit):
    """Stream response for UI thinking tokens, accumulate into complete message, and handle network retries."""
    last_exc = None

    for attempt in range(1, MAX_STREAM_RETRIES + 1):
        try:
            response_stream = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=16384,
                stream=True,
            )

            full_content = ""
            tool_calls_map: dict[int, dict[str, Any]] = {}
            finish_reason = None

            for chunk in response_stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                if choice.finish_reason:
                    finish_reason = choice.finish_reason

                # Gather text content for message history (do not stream to UI)
                if delta.content:
                    full_content += delta.content

                # Accumulate tool call deltas
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": tc_delta.id or "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        tc = tool_calls_map[idx]
                        if tc_delta.id:
                            tc["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tc["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                tc["function"]["arguments"] += (
                                    tc_delta.function.arguments
                                )
                                emit("agent", "running", extra={"thinking": tc_delta.function.arguments})

            # Sort by index
            tool_calls = [tool_calls_map[idx] for idx in sorted(tool_calls_map.keys())]

            # Ensure each tool call has an ID
            for tc in tool_calls:
                if not tc["id"]:
                    tc["id"] = "call_" + os.urandom(4).hex()

            return full_content, tool_calls, finish_reason

        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            wait_time = 2**attempt  # 2s, 4s, 8s
            logger.warning(
                f"Transient network error on attempt {attempt}/{MAX_STREAM_RETRIES}: {exc}. "
                f"Retrying in {wait_time}s..."
            )
            emit(
                "agent",
                "warning",
                f"Network error (attempt {attempt}/{MAX_STREAM_RETRIES}), retrying in {wait_time}s...",
            )
            time.sleep(wait_time)

    # All retries exhausted
    raise last_exc


def run_agent(
    uploaded_files: dict[str, str],
    theme_name: str,
    theme_slug: str,
    author: str,
    workspace: Path,
    emit: Callable,
):
    """Main agent loop. Runs synchronously in a background thread."""

    output_dir = workspace / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"=== Starting agent for theme: {theme_name} ===")
    emit("agent", "running", f"Starting theme generation for '{theme_name}'")

    emit("agent", "running", "Seeding workspace with _s base theme...")
    seed_result = seed_workspace_with_base_theme(
        workspace=workspace,
        theme_name=theme_name,
        theme_slug=theme_slug,
        author=author,
    )
    if not seed_result.get("ok"):
        emit("agent", "error", f"Failed to seed base theme: {seed_result.get('error')}")
        return list_files(workspace)

    logger.info(
        f"  Base theme seeded: {seed_result['total_files']} files, {seed_result['files_modified']} modified"
    )
    emit(
        "agent",
        "complete",
        f"Base theme ready ({seed_result['total_files']} files pre-loaded)",
    )

    base_files_result = list_base_theme_files()
    base_theme_files = (
        base_files_result.get("files", []) if base_files_result.get("ok") else []
    )

    system_prompt = build_system_prompt(
        uploaded_files=uploaded_files,
        theme_name=theme_name,
        theme_slug=theme_slug,
        author=author,
        base_theme_files=base_theme_files,
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": "Read the uploaded files and convert them into a WordPress theme by modifying the pre-seeded _s base theme. Use copy_file and copy_section to save tokens where possible. Lint all PHP files after modification.",
        },
    ]

    max_iterations = 60  # Increased for multi-page support
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"--- Iteration {iteration} ---")
        emit("agent", "running", f"Thinking... (turn {iteration})")

        try:
            # Stream the response (Fireworks requires stream=true for max_tokens > 4096)
            # but collect everything before processing tool calls
            full_content, tool_calls, finish_reason = _stream_and_collect(
                messages, emit
            )

            logger.info(
                f"  finish_reason={finish_reason}, content_len={len(full_content)}, tool_calls={len(tool_calls)}"
            )
            if full_content:
                logger.info(f"  Agent text: {full_content[:150]}...")

            # Build the assistant message for conversation history
            ai_msg: dict[str, Any] = {
                "role": "assistant",
                "content": full_content or None,
            }
            if tool_calls:
                ai_msg["tool_calls"] = tool_calls
            messages.append(ai_msg)

            # No tool calls — agent is done
            if not tool_calls:
                logger.info("No tool calls — agent finished.")
                emit("agent", "warning", "No tool calls returned — stopping")
                break

            # Check if response was truncated (finish_reason == "length")
            # If so, the last tool call's arguments are likely incomplete
            if finish_reason == "length" and tool_calls:
                logger.warning("Response was truncated (finish_reason=length)")
                # Mark the last tool call as potentially truncated
                last_tc = tool_calls[-1]
                last_args = last_tc["function"]["arguments"]
                try:
                    json.loads(last_args)
                except json.JSONDecodeError:
                    logger.warning(
                        f"  Last tool call '{last_tc['function']['name']}' has truncated args — telling model to retry"
                    )
                    # Respond with error to tell model to retry
                    tool_results = []
                    for tc in tool_calls[:-1]:
                        # Process non-truncated tool calls normally
                        name = tc["function"]["name"]
                        try:
                            args = json.loads(tc["function"]["arguments"])
                            result_str = dispatch_tool(name, args, workspace, emit)
                        except json.JSONDecodeError:
                            result_str = json.dumps(
                                {"ok": False, "error": "Invalid JSON"}
                            )
                        tool_results.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": result_str,
                            }
                        )
                    # For the truncated one, return an error
                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": last_tc["id"],
                            "content": json.dumps(
                                {
                                    "ok": False,
                                    "error": "Your response was cut off mid-way. The file content was truncated. Please call write_file again for this file, or use copy_file/copy_section to avoid large content.",
                                }
                            ),
                        }
                    )
                    messages.extend(tool_results)
                    continue

            # Process each tool call normally
            tool_results = []
            done = False

            for tc in tool_calls:
                name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]

                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    logger.error(f"Bad JSON for {name}: {raw_args[:200]}...")
                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(
                                {
                                    "ok": False,
                                    "error": "Invalid JSON in tool arguments. Please try the call again.",
                                }
                            ),
                        }
                    )
                    continue

                result_str = dispatch_tool(name, args, workspace, emit)
                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_str,
                    }
                )

                if name == "task_complete":
                    done = True

            messages.extend(tool_results)

            if done:
                logger.info("=== Agent completed all tasks ===")
                break

        except _RETRYABLE_EXCEPTIONS as e:
            # Transient network error — retry the iteration (don't break)
            logger.warning(
                f"Retryable error in iteration {iteration} (will retry): {e}"
            )
            emit("agent", "warning", f"Network error, retrying turn {iteration}...")
            time.sleep(2)
            iteration -= 1  # Don't count this as an iteration
            continue

        except Exception as e:
            logger.error(
                f"Error in iteration {iteration}: {e}\n{traceback.format_exc()}"
            )
            emit("agent", "error", f"Error: {str(e)}")
            break

    _validate_output(output_dir, emit)

    return list_files(workspace)


def _validate_output(output_dir: Path, emit: Callable) -> None:
    """Run quick sanity checks on generated theme output and auto-fix common mistakes."""
    import re

    if not output_dir.exists():
        return

    issues = []

    for filepath in output_dir.rglob("*.php"):
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        rel = str(filepath.relative_to(output_dir))

        # Check 1: Duplicate <body> tags in page templates (not header.php)
        if filepath.name != "header.php":
            body_tags = re.findall(r"<body[\s>]", content)
            if body_tags:
                # Auto-fix: remove the duplicate <body...> tag
                fixed = re.sub(r"\n?<body[^>]*>\s*\n?", "\n", content, count=1)
                if fixed != content:
                    filepath.write_text(fixed, encoding="utf-8")
                    issues.append(f"FIXED: Removed duplicate <body> tag from {rel}")
                    logger.warning(f"  Auto-fixed: removed duplicate <body> from {rel}")

        # Check 2: Leftover _S_VERSION references
        if "_S_VERSION" in content:
            issues.append(
                f"WARNING: {rel} still contains '_S_VERSION' (undefined constant)"
            )
            logger.warning(f"  {rel} contains undeclared _S_VERSION constant")

    if issues:
        emit(
            "agent",
            "warning",
            f"Post-validation found {len(issues)} issue(s): {'; '.join(issues[:3])}",
        )
    else:
        logger.info("Post-validation: no issues found")
