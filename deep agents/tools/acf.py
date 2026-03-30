import logging
import json
import hashlib
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from ._paths import WORKSPACE_ROOT, resolve_workspace

logger = logging.getLogger("wp-agent")


@tool
def generate_acf_fields(
    template: Annotated[str, "Template file (e.g. 'front-page.php', 'header.php')"],
    content_areas: Annotated[
        list[dict], "List of fields with name, type, label, and optional sub_fields"
    ],
    scope: Annotated[
        str, "'template' for page-specific, 'global' for site-wide options"
    ] = "template",
    theme_slug: Annotated[str, "Theme folder name"] = "theme",
) -> dict:
    """Generate ACF field group JSON for editable content. Handles all JSON wiring automatically."""
    logger.info(
        f"[TOOL] generate_acf_fields(template='{template}', scope='{scope}', theme_slug='{theme_slug}')"
    )
    logger.info(f"[TOOL] Content areas: {len(content_areas)} fields")

    workspace = WORKSPACE_ROOT
    full = resolve_workspace(theme_slug, workspace)

    if not full:
        logger.error(f"[TOOL] Invalid theme path: {theme_slug}")
        return {"ok": False, "error": f"Invalid theme path: {theme_slug}"}

    acf_dir = full / "acf-json"
    acf_dir.mkdir(parents=True, exist_ok=True)

    if not content_areas:
        logger.error("[TOOL] No content_areas provided")
        return {"ok": False, "error": "No content_areas provided"}

    group_key = _generate_key(f"{scope}_{template}_{theme_slug}")
    field_group = _build_field_group(
        group_key=group_key,
        title=f"{_format_title(template)} Fields"
        if scope == "template"
        else "Theme Options",
        fields=content_areas,
        location=_build_location(template, scope),
        theme_slug=theme_slug,
    )

    json_file = f"group_{group_key.split('_')[1]}.json"
    json_path = acf_dir / json_file
    json_path.write_text(json.dumps(field_group, indent=4), encoding="utf-8")

    _update_functions_php(full)

    logger.info(f"[TOOL] ACF fields generated: {json_file}")
    logger.info(f"[TOOL] Fields: {[f.get('name') for f in content_areas]}")

    return {
        "ok": True,
        "template": template,
        "scope": scope,
        "fields_generated": len(content_areas),
        "json_file": f"{theme_slug}/acf-json/{json_file}",
    }


def _generate_key(identifier: str) -> str:
    hash_suffix = hashlib.md5(identifier.encode()).hexdigest()[:8]
    return f"group_{hash_suffix}"


def _generate_field_key(field_name: str, group_key: str) -> str:
    hash_suffix = hashlib.md5(f"{group_key}_{field_name}".encode()).hexdigest()[:8]
    return f"field_{hash_suffix}"


def _format_title(template: str) -> str:
    return template.replace(".php", "").replace("-", " ").replace("_", " ").title()


def _build_location(template: str, scope: str) -> list:
    if scope == "global":
        return [[{"param": "options_page", "operator": "==", "value": "theme-options"}]]
    if template == "front-page.php":
        return [[{"param": "page_type", "operator": "==", "value": "front_page"}]]
    return [[{"param": "page_template", "operator": "==", "value": template}]]


def _get_field_config(field_type: str) -> dict:
    configs = {
        "text": {"default_value": "", "placeholder": ""},
        "textarea": {"default_value": "", "rows": 4, "new_lines": "br"},
        "number": {"default_value": "", "min": "", "max": ""},
        "email": {"default_value": ""},
        "url": {"default_value": ""},
        "true_false": {"message": "", "default_value": 0},
        "select": {"choices": {}, "return_format": "value"},
        "image": {"return_format": "url", "preview_size": "medium", "library": "all"},
        "file": {"return_format": "url", "library": "all"},
        "link": {"return_format": "array"},
        "wysiwyg": {"tabs": "all", "toolbar": "full", "media_upload": 1},
        "repeater": {"layout": "table", "button_label": "Add Row", "sub_fields": []},
        "group": {"layout": "block", "sub_fields": []},
        "color_picker": {"default_value": "", "enable_opacity": 0},
    }
    return configs.get(field_type, {})


def _build_field_group(
    group_key: str, title: str, fields: list[dict], location: list, theme_slug: str
) -> dict:
    def process_fields(field_list: list[dict], parent_key: str) -> list[dict]:
        result = []
        for field in field_list:
            name = field.get("name", "")
            ftype = field.get("type", "text")
            label = field.get("label", name.replace("_", " ").title())

            config = {
                "key": _generate_field_key(name, parent_key),
                "label": label,
                "name": name,
                "type": ftype,
                "required": 0,
                "wrapper": {"width": "", "class": "", "id": ""},
            }
            config.update(_get_field_config(ftype))

            if "sub_fields" in field:
                config["sub_fields"] = process_fields(
                    field["sub_fields"], config["key"]
                )

            result.append(config)
        return result

    return {
        "key": group_key,
        "title": title,
        "fields": process_fields(fields, group_key),
        "location": location,
        "menu_order": 0,
        "position": "normal",
        "style": "default",
        "label_placement": "top",
        "instruction_placement": "label",
        "hide_on_screen": "",
        "active": 1,
        "description": f"Fields for {theme_slug}",
        "show_in_rest": 0,
    }


def _update_functions_php(theme_dir: Path) -> None:
    functions_file = theme_dir / "functions.php"

    acf_code = """
// ACF JSON sync
add_filter('acf/settings/save_json', function($path) {
    return get_stylesheet_directory() . '/acf-json';
});
add_filter('acf/settings/load_json', function($paths) {
    unset($paths[0]);
    $paths[] = get_stylesheet_directory() . '/acf-json';
    return $paths;
});

// Theme Options page
if (function_exists('acf_add_options_page')) {
    acf_add_options_page(array(
        'page_title' => 'Theme Options',
        'menu_title' => 'Theme Options',
        'menu_slug'  => 'theme-options',
        'capability' => 'edit_posts',
        'redirect'   => false,
    ));
}
"""
    if functions_file.exists():
        content = functions_file.read_text(encoding="utf-8")
        if "acf/settings/save_json" not in content:
            functions_file.write_text(content + acf_code, encoding="utf-8")
            logger.info("[TOOL] Updated functions.php with ACF code")
    else:
        functions_file.write_text(f"<?php\n{acf_code}", encoding="utf-8")
        logger.info("[TOOL] Created functions.php with ACF code")
