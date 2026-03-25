TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the theme folder. Use for creating or modifying files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to workspace (e.g., 'theme-slug/header.php')",
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
            "description": "Read a file. Use 'uploads/filename' for uploaded source files, 'theme-slug/filename' for theme files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path (e.g., 'uploads/index.html' or 'theme-slug/style.css')",
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
            "description": "List all files in the workspace (uploads + theme-slug) with sizes.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file directly without outputting its content. Saves tokens. Source can be 'base_theme/...', 'uploads/...', or 'theme-slug/...'. Destination is always relative to workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Source file path (e.g., 'base_theme/sidebar.php', 'uploads/logo.png')",
                    },
                    "dest": {
                        "type": "string",
                        "description": "Destination path (e.g., 'theme-slug/sidebar.php', 'theme-slug/assets/images/logo.png')",
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
            "description": "Extract a section between two regex patterns from a source file and write/append to a destination. Works for CSS, JS, HTML, PHP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src_file": {
                        "type": "string",
                        "description": "Source file path (supports 'base_theme/', 'uploads/', 'theme-slug/')",
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
            "description": "Search for a regex pattern in a single file. Returns matching lines with line numbers.",
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
            "description": "Search across ALL workspace files for a regex pattern. Returns matching files and lines.",
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
            "description": "Check a PHP file for syntax errors and WordPress coding standards. Auto-fixes fixable issues if PHPCS is available. Call after every .php file you write or modify.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to PHP file (e.g., 'theme-slug/header.php')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_acf_fields",
            "description": "Generate ACF field group JSON files for editable content areas. Creates JSON files in acf-json/ folder that can be version controlled. Use this to make content editable via WordPress admin instead of hardcoded HTML.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "description": "Template file to make editable (e.g., 'front-page.php', 'header.php')",
                    },
                    "content_areas": {
                        "type": "array",
                        "description": "List of content areas to make editable. Each item: {'name': 'field_name', 'type': 'text|image|link|color_picker|textarea|true_false|select', 'label': 'Optional Label'}",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Field name (e.g., 'hero_title')",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Field type: text, textarea, image, link, color_picker, true_false, select, wysiwyg",
                                },
                                "label": {
                                    "type": "string",
                                    "description": "Optional label (defaults to formatted name)",
                                },
                            },
                            "required": ["name", "type"],
                        },
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["template", "global"],
                        "description": "'template' for per-template fields (shows on specific page template), 'global' for theme-wide options (shows on options page)",
                    },
                    "theme_slug": {
                        "type": "string",
                        "description": "Theme slug (e.g., 'my-theme'). Defaults to theme folder name.",
                    },
                },
                "required": ["template", "content_areas", "scope"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Make targeted search-and-replace edits to an existing file. "
                "Each edit specifies 'old_text' (must appear in the file) and 'new_text'. "
                "Much more token-efficient than write_file for small changes — prefer it for PHPCS fixes. "
                "Supports fuzzy matching (ignores trailing whitespace differences). "
                "Set replace_all=true to replace every occurrence (e.g. rename a variable)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to workspace (e.g. 'my-theme/header.php')",
                    },
                    "edits": {
                        "type": "array",
                        "description": "List of edits to apply sequentially",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_text": {
                                    "type": "string",
                                    "description": "Exact text to find in the file (must be unique unless replace_all=true)",
                                },
                                "new_text": {
                                    "type": "string",
                                    "description": "Replacement text",
                                },
                                "replace_all": {
                                    "type": "boolean",
                                    "description": "If true, replace every occurrence. Default: false.",
                                },
                            },
                            "required": ["old_text", "new_text"],
                        },
                    },
                },
                "required": ["path", "edits"],
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
