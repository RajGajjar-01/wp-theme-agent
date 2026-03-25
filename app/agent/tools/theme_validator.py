import subprocess
import re
from pathlib import Path

def validate_theme(workspace: Path) -> dict:
    """
    Perform structural validation on the generated WordPress theme.
    Returns a list of errors and warnings.
    """
    if not workspace.exists():
        return {"ok": False, "error": "Workspace not found"}

    # Get the theme directory (the first subdirectory that is not .gemini or __pycache__)
    theme_dirs = [p for p in workspace.iterdir() if p.is_dir() and not p.name.startswith(('.', '__'))]
    if not theme_dirs:
        return {"ok": False, "error": "No theme directory found in workspace"}
    
    theme_dir = theme_dirs[0]
    theme_slug = theme_dir.name
    
    results = {
        "ok": True,
        "theme_slug": theme_slug,
        "errors": [],
        "warnings": [],
        "checks_passed": 0,
        "checks_total": 0
    }

    # 1. Required Files
    required = ["style.css", "functions.php", "header.php", "footer.php", "index.php"]
    for f in required:
        results["checks_total"] += 1
        if not (theme_dir / f).exists():
            results["errors"].append(f"Missing required file: {f}")
            results["ok"] = False
        else:
            results["checks_passed"] += 1

    # 2. PHP Syntax Check
    for php_file in theme_dir.rglob("*.php"):
        results["checks_total"] += 1
        res = subprocess.run(["php", "-l", str(php_file)], capture_output=True, text=True)
        if res.returncode != 0:
            results["errors"].append(f"Syntax error in {php_file.relative_to(theme_dir)}: {res.stdout.strip()}")
            results["ok"] = False
        else:
            results["checks_passed"] += 1

    # 3. Structural Integrity (wp_head, wp_footer, body_class)
    header_file = theme_dir / "header.php"
    if header_file.exists():
        content = header_file.read_text(encoding="utf-8")
        results["checks_total"] += 3
        if "wp_head()" not in content:
            results["errors"].append("header.php: Missing wp_head() before </head>")
            results["ok"] = False
        else:
            results["checks_passed"] += 1
        
        if "body_class()" not in content:
            results["errors"].append("header.php: Missing body_class() in <body> tag")
            results["ok"] = False
        else:
            results["checks_passed"] += 1
        
        if "wp_body_open()" not in content:
            results["warnings"].append("header.php: Missing wp_body_open() after <body>")
        else:
            results["checks_passed"] += 1

    footer_file = theme_dir / "footer.php"
    if footer_file.exists():
        content = footer_file.read_text(encoding="utf-8")
        results["checks_total"] += 1
        if "wp_footer()" not in content:
            results["errors"].append("footer.php: Missing wp_footer() before </body>")
            results["ok"] = False
        else:
            results["checks_passed"] += 1

    # 4. No Hardcoded Page Content
    for tmpl in theme_dir.glob("*.php"):
        if tmpl.name in ["header.php", "footer.php", "functions.php", "index.php"]:
            continue
        content = tmpl.read_text(encoding="utf-8")
        
        # Look for hardcoded strings in HTML (excluding tags/PHP)
        hardcoded = re.findall(r'>(?![<\?\s])([^<\{\}]+)<', content)
        for text in hardcoded:
            text = text.strip()
            if len(text) > 30 and "get_field" not in content and "get_sub_field" not in content:
                results["warnings"].append(f"{tmpl.name}: Potential hardcoded content found: \"{text[:30]}...\". Use ACF fields instead.")
                break

    # 5. Functions.php Enqueue
    func_file = theme_dir / "functions.php"
    if func_file.exists():
        content = func_file.read_text(encoding="utf-8")
        results["checks_total"] += 1
        if "wp_enqueue_scripts" not in content:
            results["errors"].append("functions.php: No scripts/styles enqueued via wp_enqueue_scripts action")
            results["ok"] = False
        else:
            results["checks_passed"] += 1

    return results
