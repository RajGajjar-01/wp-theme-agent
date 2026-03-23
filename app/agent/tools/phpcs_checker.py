"""PHPCS detection, execution, and auto-fix functionality.

This module provides a singleton PHPCSChecker class that handles:
- Detection of PHPCS/PHPCBF installation
- Version and standards detection
- Running PHPCS checks with JSON output
- Auto-fixing with PHPCBF
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agent.phpcs")


class PHPCSChecker:
    """Singleton class for PHPCS operations."""

    _instance: Optional["PHPCSChecker"] = None

    def __new__(cls) -> "PHPCSChecker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._phpcs_path: Optional[str] = None
        self._phpcbf_path: Optional[str] = None
        self._phpcs_version: Optional[str] = None
        self._standards: list[str] = []
        self._initialized = True
        self._checked = False

    def is_available(self) -> bool:
        """Check if PHPCS is installed and accessible.

        Returns:
            True if PHPCS is available, False otherwise.
        """
        if self._checked:
            return self._phpcs_path is not None

        self._phpcs_path = self._find_executable("phpcs")
        self._phpcbf_path = self._find_executable("phpcbf")

        if self._phpcs_path:
            self._phpcs_version = self._get_version()
            self._standards = self._get_installed_standards()
            logger.info(
                f"PHPCS found at {self._phpcs_path}, version {self._phpcs_version}"
            )
        else:
            logger.info("PHPCS not found - will use php -l only")

        self._checked = True
        return self._phpcs_path is not None

    def _find_executable(self, name: str) -> Optional[str]:
        """Find executable in common locations.

        Checks in order:
        1. Local vendor/bin (Composer project install)
        2. System PATH
        3. ~/.composer/vendor/bin (global Composer install)
        4. /usr/local/bin (common system install)

        Args:
            name: Executable name (phpcs or phpcbf).

        Returns:
            Path to executable or None if not found.
        """
        # Get project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent

        locations = [
            str(project_root / "vendor" / "bin" / name),
            shutil.which(name),
            os.path.expanduser(f"~/.composer/vendor/bin/{name}"),
            f"/usr/local/bin/{name}",
            f"/usr/bin/{name}",
        ]

        for location in locations:
            if location and self._test_executable(location):
                return location

        return None

    def _test_executable(self, path: str) -> bool:
        """Test if an executable exists and runs.

        Args:
            path: Path to executable.

        Returns:
            True if executable runs successfully.
        """
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return False

    def _get_version(self) -> Optional[str]:
        """Get PHPCS version.

        Returns:
            Version string or None if not available.
        """
        if not self._phpcs_path:
            return None

        try:
            result = subprocess.run(
                [self._phpcs_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Output format: "PHP_CodeSniffer version 3.8.0 (stable) by Squiz Labs"
                output = result.stdout.strip()
                if "version" in output:
                    return output.split("version")[1].split()[0].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def _get_installed_standards(self) -> list[str]:
        """Get installed coding standards.

        Returns:
            List of standard names.
        """
        if not self._phpcs_path:
            return []

        try:
            result = subprocess.run(
                [self._phpcs_path, "-i"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Output format: "The installed coding standards are: WordPress, WordPress-Core, ..."
                output = result.stdout.strip()
                if ":" in output:
                    standards_str = output.split(":")[1].strip()
                    return [s.strip() for s in standards_str.split(",")]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return []

    def get_standards(self) -> list[str]:
        """Get available coding standards.

        Returns:
            List of standard names.
        """
        return self._standards

    def has_standard(self, standard: str) -> bool:
        """Check if a specific standard is installed.

        Args:
            standard: Standard name to check.

        Returns:
            True if standard is available.
        """
        return standard in self._standards or any(
            standard.lower() in s.lower() for s in self._standards
        )

    def check(self, path: Path, standard: str = "WordPress") -> dict:
        """Run PHPCS check on a file or directory.

        Args:
            path: Path to file or directory.
            standard: Coding standard to use.

        Returns:
            Dict with:
                - ok: True if no errors
                - error_count: Number of errors
                - warning_count: Number of warnings
                - fixable_count: Number of fixable issues
                - errors: List of error details
                - warnings: List of warning details
        """
        if not self._phpcs_path:
            return {"ok": True, "skipped": True, "message": "PHPCS not available"}

        if not path.exists():
            return {"ok": False, "error": f"Path does not exist: {path}"}

        # Use WordPress-Core if WordPress not available but Core is
        if not self.has_standard(standard):
            if self.has_standard("WordPress-Core"):
                standard = "WordPress-Core"
                logger.warning(f"Standard '{standard}' not found, using WordPress-Core")
            else:
                return {
                    "ok": False,
                    "error": f"Coding standard '{standard}' not installed",
                }

        try:
            result = subprocess.run(
                [
                    self._phpcs_path,
                    f"--standard={standard}",
                    "--report=json",
                    "--no-progress",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # PHPCS returns non-zero when errors found
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                # If not JSON, return raw output
                return {
                    "ok": result.returncode == 0,
                    "raw_output": result.stdout[:1000]
                    if result.stdout
                    else result.stderr[:1000],
                }

            totals = data.get("totals", {})
            error_count = totals.get("errors", 0)
            warning_count = totals.get("warnings", 0)
            fixable_count = totals.get("fixable", 0)

            # Extract errors and warnings for agent-friendly output
            errors = []
            warnings = []

            for file_path, file_data in data.get("files", {}).items():
                for msg in file_data.get("messages", []):
                    item = {
                        "file": file_path,
                        "line": msg.get("line", 0),
                        "column": msg.get("column", 0),
                        "message": msg.get("message", ""),
                        "source": msg.get("source", ""),
                        "fixable": msg.get("fixable", False),
                    }
                    if msg.get("type") == "ERROR":
                        errors.append(item)
                    else:
                        warnings.append(item)

            return {
                "ok": error_count == 0,
                "error_count": error_count,
                "warning_count": warning_count,
                "fixable_count": fixable_count,
                "errors": errors[:20],  # Limit for token efficiency
                "warnings": warnings[:10],
            }

        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "PHPCS check timed out"}
        except Exception as e:
            return {"ok": False, "error": f"PHPCS check failed: {str(e)}"}

    def fix(self, path: Path, standard: str = "WordPress") -> dict:
        """Run PHPCBF to auto-fix issues.

        Args:
            path: Path to file or directory.
            standard: Coding standard to use.

        Returns:
            Dict with:
                - ok: True if fix successful
                - fixed: Number of issues fixed
                - remaining: Number of issues remaining
        """
        if not self._phpcbf_path:
            return {"ok": False, "error": "PHPCBF not available"}

        if not path.exists():
            return {"ok": False, "error": f"Path does not exist: {path}"}

        # Use WordPress-Core if WordPress not available
        if not self.has_standard(standard):
            if self.has_standard("WordPress-Core"):
                standard = "WordPress-Core"
            else:
                return {
                    "ok": False,
                    "error": f"Coding standard '{standard}' not installed",
                }

        try:
            result = subprocess.run(
                [
                    self._phpcbf_path,
                    f"--standard={standard}",
                    "--no-progress",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # PHPCBF returns:
            # 0 = no fixable errors
            # 1 = fixed errors
            # 2+ = errors
            output = result.stdout + result.stderr

            # Parse output for fixed count
            # Output format: "PHPCBF RESULT SUMMARY"
            # "A TOTAL OF X ERROR(S) WERE FIXED"
            fixed = 0
            if "WERE FIXED" in output:
                try:
                    fixed_str = output.split("A TOTAL OF")[1].split("ERROR")[0].strip()
                    fixed = int(fixed_str)
                except (IndexError, ValueError):
                    pass

            return {
                "ok": result.returncode in (0, 1),
                "fixed": fixed,
                "raw_output": output[:500] if output else None,
            }

        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "PHPCBF fix timed out"}
        except Exception as e:
            return {"ok": False, "error": f"PHPCBF fix failed: {str(e)}"}

    def check_and_fix(
        self, path: Path, standard: str = "WordPress", auto_fix: bool = True
    ) -> dict:
        """Check, fix, and re-check a file.

        This is the main method to use - it checks for issues,
        fixes what it can, and reports remaining issues.

        Args:
            path: Path to file.
            standard: Coding standard to use.
            auto_fix: Whether to auto-fix fixable issues.

        Returns:
            Dict with:
                - ok: True if no remaining errors
                - fixed: Number of issues fixed
                - remaining_errors: Number of errors remaining
                - remaining_warnings: Number of warnings remaining
                - issues: List of remaining issues
        """
        # Step 1: Initial check
        check_result = self.check(path, standard)

        if check_result.get("skipped"):
            return check_result

        if check_result.get("ok") and check_result.get("error_count", 0) == 0:
            # No errors, nothing to fix
            return {
                "ok": True,
                "fixed": 0,
                "remaining_errors": 0,
                "remaining_warnings": check_result.get("warning_count", 0),
                "issues": [],
            }

        fixable_count = check_result.get("fixable_count", 0)

        # Step 2: Auto-fix if enabled and fixable issues exist
        if auto_fix and fixable_count > 0 and self._phpcbf_path:
            fix_result = self.fix(path, standard)
            fixed = fix_result.get("fixed", 0)
            logger.info(f"PHPCBF fixed {fixed} issues in {path}")

            # Step 3: Re-check after fixing
            recheck_result = self.check(path, standard)

            return {
                "ok": recheck_result.get("ok", False),
                "fixed": fixed,
                "remaining_errors": recheck_result.get("error_count", 0),
                "remaining_warnings": recheck_result.get("warning_count", 0),
                "issues": recheck_result.get("errors", []),
            }

        # No fixing, just return check results
        return {
            "ok": check_result.get("ok", False),
            "fixed": 0,
            "remaining_errors": check_result.get("error_count", 0),
            "remaining_warnings": check_result.get("warning_count", 0),
            "issues": check_result.get("errors", []),
        }


# Singleton instance
checker = PHPCSChecker()
