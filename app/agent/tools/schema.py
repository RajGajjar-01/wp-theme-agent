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
            "description": "Check a PHP file for syntax errors (php -l). Call after every .php file you write or modify.",
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
            "description": (
                "Generate ACF field group JSON for editable content. Supports nested fields (Repeaters/Groups). "
                "Use type 'repeater' with 'sub_fields' for rotating/repeating content blocks like features, services, or testimonials. "
                "Handles all JSON wiring automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "description": "Template file (e.g. 'front-page.php', 'header.php')",
                    },
                    "content_areas": {
                        "type": "array",
                        "description": "List of fields. For Repeaters, include a 'sub_fields' list within the field object.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Field name"},
                                "type": {
                                    "type": "string",
                                    "description": "text, textarea, image, link, repeater, group, color_picker, true_false, select, wysiwyg",
                                },
                                "label": {"type": "string", "description": "Display label"},
                                "sub_fields": {
                                    "type": "array",
                                    "description": "List of sub-fields if type is 'repeater' or 'group'",
                                    "items": {"type": "object"},
                                },
                            },
                            "required": ["name", "type"],
                        },
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["template", "global"],
                        "description": "'template' for page-specific fields, 'global' for site-wide options.",
                    },
                    "theme_slug": {
                        "type": "string",
                        "description": "Theme folder name.",
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
                "Much more token-efficient than write_file for small changes. "
                "Supports fuzzy matching. Set replace_all=true for bulk renaming."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path (e.g. 'theme/header.php')"},
                    "edits": {
                        "type": "array",
                        "description": "List of edits to apply sequentially",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_text": {"type": "string", "description": "Exact text to find"},
                                "new_text": {"type": "string", "description": "Replacement text"},
                                "replace_all": {"type": "boolean", "description": "Replace all occurrences. Default: false."},
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
            "name": "validate_theme",
            "description": (
                "Run a comprehensive structural health check on the generated theme. "
                "Checks for required files, PHP syntax, WP hooks (wp_head/wp_footer), enqueues, and hardcoded content. "
                "MANDATORY before calling task_complete. Returns actionable errors and warnings."
            ),
            "parameters": {"type": "object", "properties": {}},
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
