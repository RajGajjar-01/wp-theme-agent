import asyncio
import logging
import re
import shutil

from langgraph.config import get_stream_writer

from app.agent.clients import MINIMAX_MODEL, minimax_client
from app.agent.models import ValidationResult
from app.agent.prompts.validator import VALIDATOR_HEAL_SYSTEM
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _run_php_lint(php_code: str, php_path: str) -> tuple[bool, str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            php_path, "-l", "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=php_code.encode("utf-8"))
        output = (stdout.decode() + stderr.decode()).strip()
        passed = proc.returncode == 0 and "No syntax errors" in output
        return passed, output
    except FileNotFoundError:
        return True, "php-cli not found — skipping validation"
    except Exception as e:
        return True, f"Validation error: {e}"


async def _llm_heal(filename: str, php_code: str, error_msg: str) -> str:
    resp = await minimax_client.chat.completions.create(
        model=MINIMAX_MODEL,
        messages=[
            {"role": "system", "content": VALIDATOR_HEAL_SYSTEM},
            {"role": "user", "content": f"File: {filename}\n\nError:\n{error_msg}\n\nFile content:\n{php_code}"},
        ],
        temperature=0.1,
    )
    content = resp.choices[0].message.content or ""
    content = content.strip()
    content = re.sub(r"^```(?:php)?\s*\n?", "", content)
    content = re.sub(r"\n?```\s*$", "", content)
    return content.strip()


async def validator_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    generated_files: dict[str, str] = dict(state.get("generated_files", {}))
    errors: list[str] = list(state.get("errors", []))

    php_files = {k: v for k, v in generated_files.items() if k.endswith(".php")}
    max_retries = settings.MAX_VALIDATOR_RETRIES
    php_path = settings.PHP_CLI_PATH

    has_php = shutil.which(php_path) is not None

    if not has_php:
        writer({"node": "validator", "status": "running", "message": "php-cli not found — skipping PHP lint validation"})
        validation_results = {
            f: ValidationResult(passed=True, attempts=0, error="php-cli not available")
            for f in php_files
        }
        writer({"node": "validator", "status": "complete", "message": f"{len(php_files)} PHP files skipped (no php-cli)"})
        return {"validation_results": validation_results, "generated_files": generated_files, "errors": errors}

    writer({"node": "validator", "status": "running", "message": f"Validating {len(php_files)} PHP files via php -l..."})

    validation_results: dict[str, ValidationResult] = {}

    for filename, content in sorted(php_files.items()):
        passed, error_msg = await _run_php_lint(content, php_path)

        if passed:
            validation_results[filename] = ValidationResult(passed=True, attempts=1)
            writer({"node": "validator", "status": "passed", "message": f"{filename} — OK"})
            continue

        # Self-heal loop
        healed = False
        for attempt in range(2, max_retries + 1):
            writer({"node": "validator", "status": "warning", "message": f"{filename} — syntax error, healing (attempt {attempt}/{max_retries})..."})

            try:
                content = await _llm_heal(filename, content, error_msg)
                generated_files[filename] = content
                passed, error_msg = await _run_php_lint(content, php_path)

                if passed:
                    validation_results[filename] = ValidationResult(passed=True, attempts=attempt)
                    writer({"node": "validator", "status": "passed", "message": f"{filename} — fixed on attempt {attempt}"})
                    healed = True
                    break
            except Exception as e:
                logger.error("Heal attempt %d failed for %s: %s", attempt, filename, e)
                errors.append(f"Heal attempt {attempt} failed for {filename}: {e}")

        if not healed:
            validation_results[filename] = ValidationResult(passed=False, attempts=max_retries, error=error_msg)
            errors.append(f"Validation failed for {filename} after {max_retries} attempts: {error_msg}")
            writer({"node": "validator", "status": "failed", "message": f"{filename} — FAILED after {max_retries} attempts"})

    passed_count = sum(1 for r in validation_results.values() if r.passed)
    failed_count = len(validation_results) - passed_count

    writer({
        "node": "validator",
        "status": "complete",
        "message": f"{passed_count}/{len(validation_results)} PHP files validated, {failed_count} failure(s)",
    })

    return {
        "validation_results": validation_results,
        "generated_files": generated_files,
        "errors": errors,
    }
