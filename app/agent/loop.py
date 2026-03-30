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
    edit_file,
    search_in_file,
    grep_workspace,
    list_base_theme_files,
    read_base_theme_file,
    seed_workspace_with_base_theme,
    generate_acf_fields,
)
from app.agent.tools.schema import TOOLS
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
                if path.endswith(".php"):
                    lint_result = run_php_lint(path, workspace)
                    if not lint_result.get("ok"):
                        emit(
                            "agent",
                            "warning",
                            f"{path} — lint error: {lint_result.get('error', '')[:80]}",
                        )
                        result["lint_ok"] = False
                        result["lint_error"] = lint_result.get("error", "")
                    else:
                        emit("agent", "complete", f"{path} — no syntax errors")
                        result["lint_ok"] = True

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
                dest = args.get("dest", "")
                if dest.endswith(".php"):
                    lint_result = run_php_lint(dest, workspace)
                    if not lint_result.get("ok"):
                        emit(
                            "agent",
                            "warning",
                            f"{dest} — lint error: {lint_result.get('error', '')[:80]}",
                        )
                        result["lint_ok"] = False
                        result["lint_error"] = lint_result.get("error", "")
                    else:
                        emit("agent", "complete", f"{dest} — no syntax errors")
                        result["lint_ok"] = True

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
                dest_file = args.get("dest_file", "")
                if dest_file.endswith(".php"):
                    lint_result = run_php_lint(dest_file, workspace)
                    if not lint_result.get("ok"):
                        emit(
                            "agent",
                            "warning",
                            f"{dest_file} — lint error: {lint_result.get('error', '')[:80]}",
                        )
                        result["lint_ok"] = False
                        result["lint_error"] = lint_result.get("error", "")
                    else:
                        emit("agent", "complete", f"{dest_file} — no syntax errors")
                        result["lint_ok"] = True

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

        elif name == "edit_file":
            result = edit_file(
                args.get("path", ""),
                args.get("edits", []),
                workspace,
            )
            if result.get("ok"):
                logger.info(
                    f"  ✓ Edited {args.get('path')} ({result.get('edits_applied', 0)} edit(s))"
                )
                emit(
                    "agent",
                    "complete",
                    f"Edited {args.get('path')} ({result.get('edits_applied', 0)} edit(s) applied)",
                )
                path = args.get("path", "")
                if path.endswith(".php"):
                    lint_result = run_php_lint(path, workspace)
                    if not lint_result.get("ok"):
                        emit(
                            "agent",
                            "warning",
                            f"{path} — lint error: {lint_result.get('error', '')[:80]}",
                        )
                        result["lint_ok"] = False
                        result["lint_error"] = lint_result.get("error", "")
                    else:
                        emit("agent", "complete", f"{path} — no syntax errors")
                        result["lint_ok"] = True

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

        elif name == "generate_acf_fields":
            theme_slug = args.get("theme_slug", "output")
            result = generate_acf_fields(
                template=args.get("template", ""),
                content_areas=args.get("content_areas", []),
                workspace=workspace,
                scope=args.get("scope", "template"),
                theme_slug=theme_slug,
            )
            if result.get("ok"):
                emit(
                    "agent",
                    "complete",
                    f"Generated ACF fields: {result.get('fields_generated')} fields in {result.get('json_file')}",
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
                                emit(
                                    "agent",
                                    "running",
                                    extra={"thinking": tc_delta.function.arguments},
                                )

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

    output_dir = workspace / theme_slug
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
            "content": "Read all uploaded files and convert them into a complete WordPress theme following the workflow in your instructions. Use token-efficient tools (edit_file, copy_section, copy_file) wherever possible. Use generate_acf_fields() to make key content areas editable.",
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
    """Run PHPCS on all PHP files + sanity checks."""
    import re
    from app.agent.tools.phpcs_checker import checker

    if not output_dir.exists():
        return

    issues = []
    phpcs_issues = []

    # 1. Run PHPCS check-and-fix on ALL PHP files
    if checker.is_available():
        for filepath in output_dir.rglob("*.php"):
            rel = str(filepath.relative_to(output_dir))
            result = checker.check_and_fix(filepath, auto_fix=True)

            if result.get("skipped"):
                continue

            fixed = result.get("fixed", 0)
            if fixed > 0:
                emit("agent", "complete", f"PHPCS auto-fixed {fixed} issue(s) in {rel}")

            remaining = result.get("remaining_errors", 0)
            if remaining > 0:
                phpcs_issues.append(f"{rel} ({remaining} errors)")
    else:
        logger.info("PHPCS not available — skipping coding standards check")

    # 2. Sanity checks — auto-fix common issues
    for filepath in output_dir.rglob("*.php"):
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        rel = str(filepath.relative_to(output_dir))

        # Check 1: Duplicate <body> tags (only header.php should have it)
        if filepath.name != "header.php":
            body_tags = re.findall(r"<body[\s>]", content)
            if body_tags:
                fixed = re.sub(r"\n?<body[^>]*>\s*\n?", "\n", content, count=1)
                if fixed != content:
                    filepath.write_text(fixed, encoding="utf-8")
                    issues.append(f"FIXED: {rel} (removed duplicate <body>)")
                    logger.warning(f"  Auto-fixed: {rel}")

        # Check 2: Leftover _S_VERSION references
        if "_S_VERSION" in content:
            theme_slug = output_dir.name
            version_const = f"{theme_slug.upper().replace('-', '_')}_VERSION"
            fixed = content.replace("_S_VERSION", version_const)
            if fixed != content:
                filepath.write_text(fixed, encoding="utf-8")
                issues.append(f"FIXED: {rel} (_S_VERSION → {version_const})")
                logger.warning(f"  Auto-fixed: {rel} _S_VERSION → {version_const}")

    # 3. Emit summary
    if phpcs_issues:
        emit("agent", "warning", f"PHPCS: {len(phpcs_issues)} files have remaining errors")

    if issues:
        emit("agent", "warning", f"Auto-fixed {len(issues)} issue(s)")

    if not phpcs_issues and not issues:
        emit("agent", "complete", "All PHP files validated ✓")

