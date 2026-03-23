import json
import hashlib
from pathlib import Path
from typing import Any

from ._paths import resolve


def generate_acf_fields(
    template: str,
    content_areas: list[dict],
    workspace: Path,
    scope: str = "template",
    theme_slug: str = "theme",
) -> dict:
    """Generate ACF field group JSON in acf-json/ folder.

    Creates version-controlled JSON files synced across WordPress environments.
    """
    full = resolve(f"{theme_slug}", workspace)
    if not full:
        return {"ok": False, "error": f"Path escape blocked: {theme_slug}"}

    acf_json_dir = full / "acf-json"
    acf_json_dir.mkdir(parents=True, exist_ok=True)

    if not content_areas:
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

    json_filename = f"group_{group_key.split('_')[1]}.json"
    json_path = acf_json_dir / json_filename

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(field_group, f, indent=4)

    _update_functionsPhp(full, scope, theme_slug)

    return {
        "ok": True,
        "template": template,
        "scope": scope,
        "fields_generated": len(content_areas),
        "json_file": str(json_path.relative_to(workspace)),
        "group_key": group_key,
    }


def _generate_key(identifier: str) -> str:
    """Generate unique ACF group key from identifier.

    Uses MD5 hash for consistent key generation."""
    hash_suffix = hashlib.md5(identifier.encode()).hexdigest()[:8]
    return f"group_{hash_suffix}"


def _generate_field_key(field_name: str, group_key: str) -> str:
    """Generate unique field key for ACF.

    Combines group_key and field_name for unique hash."""
    hash_suffix = hashlib.md5(f"{group_key}_{field_name}".encode()).hexdigest()[:8]
    return f"field_{hash_suffix}"


def _format_title(template: str) -> str:
    """Convert template filename to readable title.

    Removes .php, replaces dashes/underscores with spaces."""
    name = template.replace(".php", "").replace("-", " ").replace("_", " ").title()
    return name


def _build_location(template: str, scope: str) -> list:
    """Build ACF location rules based on scope.

    Returns template-specific or global (options page) rules."""
    if scope == "global":
        return [[{"param": "options_page", "operator": "==", "value": "theme-options"}]]
    else:
        return [[{"param": "page_template", "operator": "==", "value": template}]]


def _get_field_config(field_type: str, field_name: str, label: str) -> dict:
    """Get ACF field configuration based on type.

    Merges base config with type-specific settings."""

    base = {
        "key": "",
        "label": label,
        "name": field_name,
        "type": field_type,
        "prefix": "",
        "instructions": "",
        "required": 0,
        "conditional_logic": 0,
        "wrapper": {"width": "", "class": "", "id": ""},
    }

    type_config = {
        # Basic
        "text": {
            "default_value": "",
            "placeholder": "",
            "prepend": "",
            "append": "",
            "maxlength": "",
        },
        "textarea": {
            "default_value": "",
            "placeholder": "",
            "maxlength": "",
            "rows": 4,
            "new_lines": "br",
        },
        "number": {
            "default_value": "",
            "placeholder": "",
            "min": "",
            "max": "",
            "step": "",
        },
        "email": {"default_value": "", "placeholder": ""},
        "url": {"default_value": "", "placeholder": ""},
        "password": {"default_value": "", "placeholder": ""},
        # Selection
        "true_false": {"message": "", "default_value": 0},
        "select": {
            "choices": {},
            "allow_null": 0,
            "multiple": 0,
            "ui": 0,
            "return_format": "value",
        },
        "radio": {
            "choices": {},
            "other_choice": 0,
            "save_other_choice": 0,
            "return_format": "value",
        },
        "checkbox": {
            "choices": {},
            "allow_custom": 0,
            "save_custom": 0,
            "return_format": "value",
        },
        "button_group": {"choices": {}, "allow_null": 0, "return_format": "value"},
        # Media
        "image": {"return_format": "url", "preview_size": "medium", "library": "all"},
        "file": {"return_format": "url", "library": "all"},
        "gallery": {"return_format": "array", "preview_size": "medium"},
        # Content
        "link": {"return_format": "array"},
        "wysiwyg": {"tabs": "all", "toolbar": "full", "media_upload": 1},
        "oembed": {"width": "", "height": ""},
        # Date/Time
        "date_picker": {
            "display_format": "d/m/Y",
            "return_format": "d/m/Y",
            "first_day": 1,
        },
        "time_picker": {"display_format": "H:i", "return_format": "H:i"},
        "date_time_picker": {
            "display_format": "d/m/Y H:i",
            "return_format": "d/m/Y H:i",
            "first_day": 1,
        },
        # Layout
        "repeater": {"collapsed": "", "min": 0, "max": 0, "layout": "table"},
        "flexible_content": {"layouts": [], "min": "", "max": ""},
        "group": {"sub_fields": []},
        # Advanced
        "google_map": {"center_lat": "", "center_lng": "", "zoom": ""},
        "taxonomy": {
            "taxonomy": "category",
            "field_type": "checkbox",
            "return_format": "id",
        },
        "user": {"role": [], "return_format": "id"},
        "post_object": {"post_type": [], "return_format": "id"},
        "relationship": {
            "post_type": [],
            "filters": ["search", "taxonomy"],
            "return_format": "id",
        },
        # Other
        "color_picker": {"default_value": "", "enable_opacity": 0},
        "range": {"default_value": 50, "min": 0, "max": 100, "step": 1},
        "message": {"message": "", "esc_html": 0},
    }

    if field_type in type_config:
        base.update(type_config[field_type])
    return base


def _build_field_group(
    group_key: str, title: str, fields: list[dict], location: list, theme_slug: str
) -> dict:
    """Build complete ACF field group array.

    Includes location rules, field configs, and metadata."""
    acf_fields = []
    for field in fields:
        fname, ftype, flabel = (
            field.get("name", ""),
            field.get("type", "text"),
            field.get("label", field.get("name", "").replace("_", " ").title()),
        )
        fc = _get_field_config(ftype, fname, flabel)
        fc["key"] = _generate_field_key(fname, group_key)
        acf_fields.append(fc)

    return {
        "key": group_key,
        "title": title,
        "fields": acf_fields,
        "location": location,
        "menu_order": 0,
        "position": "normal",
        "style": "default",
        "label_placement": "top",
        "instruction_placement": "label",
        "hide_on_screen": "",
        "active": 1,
        "description": f"Auto-generated fields for {theme_slug}",
        "show_in_rest": 0,
    }


def _update_functionsPhp(theme_dir: Path, scope: str, theme_slug: str) -> None:
    """Add ACF initialization code to functions.php.

    Adds JSON save/load paths and optionally creates options page."""
    functions_file = theme_dir / "functions.php"

    acf_code = """
// ACF JSON Settings
add_filter('acf/settings/save_json', function($path) {
    return get_stylesheet_directory() . '/acf-json';
});
add_filter('acf/settings/load_json', function($paths) {
    unset($paths[0]);
    $paths[] = get_stylesheet_directory() . '/acf-json';
    return $paths;
});

// Load ACF JSON fields programmatically
$acf_json_path = get_stylesheet_directory() . '/acf-json';
if (is_dir($acf_json_path)) {
    $json_files = glob($acf_json_path . '/*.json');
    if (!empty($json_files)) {
        foreach ($json_files as $file) {
            $json = json_decode(file_get_contents($file), true);
            if ($json && isset($json['key'])) {
                acf_add_local_field_group($json);
            }
        }
    }
}
"""

    if scope == "global":
        acf_code += """
if (function_exists('acf_add_options_page')) {
    acf_add_options_page(array(
        'page_title' => 'Theme Options', 'menu_title' => 'Theme Options',
        'menu_slug' => 'theme-options', 'capability' => 'edit_posts', 'redirect' => false,
    ));
}
"""

    if functions_file.exists():
        content = functions_file.read_text(encoding="utf-8")
        if "acf/settings/save_json" not in content:
            content += acf_code
            functions_file.write_text(content, encoding="utf-8")
    else:
        functions_file.write_text(f"<?php{acf_code}", encoding="utf-8")


def get_field_code(field_name: str, field_type: str, default: str = "") -> str:
    """Generate PHP to display ACF field with fallback.

    Returns safe PHP code with esc_html/esc_url for security."""

    if field_type == "image":
        return f"""<?php $img = get_field('{field_name}'); ?>
<?php if($img): ?><img src="<?php echo esc_url($img); ?>" alt="<?php echo esc_attr(get_bloginfo('name')); ?>"><?php endif; ?>"""

    if field_type == "image_array":
        return f"""<?php $img = get_field('{field_name}'); ?>
<?php if($img): ?><img src="<?php echo esc_url($img['url']); ?>" alt="<?php echo esc_attr($img['alt']); ?>"><?php endif; ?>"""

    if field_type == "file":
        return f"""<?php $file = get_field('{field_name}'); ?>
<?php if($file): ?><a href="<?php echo esc_url($file['url']); ?>" download>Download</a><?php endif; ?>"""

    if field_type == "gallery":
        return f"""<?php $gallery = get_field('{field_name}'); ?>
<?php if($gallery): foreach($gallery as $img): ?>
<img src="<?php echo esc_url($img['sizes']['medium']); ?>" alt="<?php echo esc_attr($img['alt']); ?>">
<?php endforeach; endif; ?>"""

    if field_type == "link":
        return f"""<?php $link = get_field('{field_name}'); ?>
<?php if($link): ?><a href="<?php echo esc_url($link['url']); ?>" class="btn"<?php if($link['target']): ?> target="<?php echo esc_attr($link['target']); ?>"<?php endif; ?>><?php echo esc_html($link['title']); ?></a><?php endif; ?>"""

    if field_type == "color_picker":
        return f"""<?php $color = get_field('{field_name}'); ?><?php if($color): ?> style="color: <?php echo esc_attr($color); ?>"<?php endif; ?>"""

    if field_type == "range":
        return f"""<?php echo esc_html(get_field('{field_name}') ?: 50); ?>"""

    if field_type == "true_false":
        return f"""<?php if(get_field('{field_name}')): ?><!-- Conditional content --><?php endif; ?>"""

    if field_type == "textarea":
        return f"""<?php echo nl2br(esc_html(get_field('{field_name}') ?: '{default}')); ?>"""

    if field_type == "wysiwyg":
        return f"""<?php echo get_field('{field_name}'); ?>"""

    if field_type == "oembed":
        return f"""<?php echo get_field('{field_name}'); ?>"""

    if field_type == "date_picker":
        return f"""<?php echo esc_html(get_field('{field_name}')); ?>"""

    if field_type == "select" or field_type == "radio" or field_type == "button_group":
        return f"""<?php echo esc_html(get_field('{field_name}')); ?>"""

    if field_type == "checkbox":
        return f"""<?php $values = get_field('{field_name}'); ?>
<?php if($values): ?><?php foreach($values as $val): ?><span><?php echo esc_html($val); ?></span><?php endforeach; endif; ?>"""

    if field_type == "number" or field_type == "range":
        return f"""<?php echo esc_html(get_field('{field_name}') ?: 0); ?>"""

    if field_type == "email":
        return f"""<?php echo esc_html(get_field('{field_name}')); ?>"""

    if field_type == "url":
        return f"""<?php $url = get_field('{field_name}'); ?>
<?php if($url): ?><a href="<?php echo esc_url($url); ?>">Link</a><?php endif; ?>"""

    if default:
        return f"""<?php echo esc_html(get_field('{field_name}') ?: '{default}'); ?>"""
    return f"""<?php echo esc_html(get_field('{field_name}')); ?>"""
