# WordPress Theme Generator - Deep Agents

A multi-agent WordPress theme generator built with LangChain's Deep Agents framework.

## Architecture

```
deep agents/
├── app.py                    # Entry point + CLI
├── agents/
│   ├── __init__.py           # Main agent + generate_theme()
│   └── sub_agents.py         # Specialized sub-agents
├── tools/
│   ├── __init__.py           # Tool registry
│   ├── _paths.py             # Path resolution
│   ├── base_theme.py         # _s theme operations
│   ├── php_checker.py        # PHP lint + PHPCS
│   ├── acf.py                # ACF field generation
│   └── theme_validator.py    # Theme validation
├── prompts/
│   ├── __init__.py
│   └── orchestrator_prompt.py
├── base_theme/               # _s starter theme
└── workspaces/               # Generated themes
```

## Agent Architecture

### Single Agent Mode (Default)
```
User → Orchestrator Agent → Tools → WordPress Theme
```

### Multi-Agent Mode (--multi flag)
```
User → Orchestrator
          ├── Analyzer Sub-agent (parse HTML/CSS)
          ├── Generator Sub-agent (create PHP)
          ├── ACF Designer Sub-agent (field groups)
          └── Validator Sub-agent (quality check)
```

## Built-in Tools (from Deep Agents)

- `write_todos` - Task planning
- `read_file`, `write_file`, `edit_file` - File operations
- `ls`, `glob`, `grep` - File discovery
- `execute` - Shell commands
- `task` - Spawn sub-agents

## Custom Tools (WordPress-specific)

| Tool | Purpose |
|------|---------|
| `seed_base_theme` | Copy _s theme with slug replacements |
| `list_base_theme_files` | List available _s files |
| `read_base_theme_file` | Read _s template |
| `run_php_lint` | PHP syntax check |
| `run_phpcs` | WordPress coding standards |
| `generate_acf_fields` | Create ACF field groups |
| `validate_theme` | Comprehensive theme validation |

## Usage

```bash
# Basic usage (single agent)
cd "deep agents"
python app.py

# Multi-agent mode
python app.py --multi

# Custom theme
python app.py --theme "My Theme" --slug my-theme --author "John Doe"
```

## Programmatic Usage

```python
from agents import generate_theme

result = generate_theme(
    theme_name="My Theme",
    theme_slug="my-theme",
    author="Developer",
    uploaded_files={
        "index.html": open("index.html").read(),
        "style.css": open("style.css").read(),
    },
    use_sub_agents=True,  # Optional
)

print(f"Theme created at: {result['theme_path']}")
```

## Requirements

- Python 3.11+
- PHP (for linting)
- `deepagents` package
- `FIREWORKS_API_KEY` in .env

## Workflow

1. **Setup**: `seed_base_theme()` initializes theme from _s
2. **Analyze**: Read uploaded files, identify structure
3. **Build**: Modify header.php, footer.php, create templates
4. **Style**: Add CSS to style.css, enqueue scripts
5. **ACF**: Generate editable field groups
6. **Validate**: PHP lint + theme structure check
7. **Output**: Complete WordPress theme