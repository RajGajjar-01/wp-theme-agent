"""Sub-agents for specialized tasks.

Each sub-agent is spawned by the orchestrator using the `task` tool.
They have isolated context windows and focused responsibilities.
"""

import os
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

from tools import WP_TOOLS

ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = ROOT / "workspaces"


ANALYZER_PROMPT = """You are a theme structure analyzer. Analyze uploaded HTML/CSS files and extract:

1. **Page Structure**: Identify sections, navigation, header, footer, content areas
2. **Components**: Extract reusable components (cards, grids, forms, buttons)
3. **Styles**: List colors, fonts, spacing patterns
4. **Assets**: Identify external dependencies (Google Fonts, CDNs, libraries)

Return a structured JSON analysis that the generator can use.

Focus only on analysis. Do not write any files.
"""


GENERATOR_PROMPT = """You are a WordPress theme generator. Create PHP template files:

1. **Templates**: front-page.php, page templates, header.php, footer.php
2. **Styles**: Update style.css with uploaded CSS
3. **Scripts**: Set up functions.php with wp_enqueue_scripts

Follow WordPress standards:
- Every template: get_header() ... get_footer()
- Escape all output: esc_html(), esc_url(), esc_attr()
- Use get_template_directory_uri() for assets

Run run_php_lint() after each file written.
"""


ACF_DESIGNER_PROMPT = """You are an ACF field designer. Create field groups for editable content:

1. **Template Fields**: For each section, create appropriate fields (text, image, link, repeater)
2. **Global Fields**: Site-wide options (logo, social links, footer text)
3. **Repeating Content**: Features, services, testimonials → use repeater fields

Use generate_acf_fields() tool. Never write ACF JSON manually.

Field patterns:
- Text: get_field('name') ?: 'default'
- Image: $img = get_field('name'); if($img): <img src="<?php echo esc_url($img); ?>">
- Repeater: have_rows('name') while have_rows(): the_row(); get_sub_field('item')
"""


VALIDATOR_PROMPT = """You are a theme validator. Check the generated theme:

1. **Required Files**: style.css, functions.php, header.php, footer.php, index.php
2. **PHP Syntax**: Run run_php_lint() on all .php files
3. **WP Hooks**: wp_head() in header, wp_footer() in footer, body_class() on body
4. **Enqueues**: wp_enqueue_scripts action in functions.php
5. **ACF Fields**: Verify get_field() usage, no hardcoded content

Use validate_theme() for comprehensive check.
Report all errors clearly. Do not fix them - report only.
"""


def _create_model(model_name: str = "accounts/fireworks/models/glm-5") -> ChatOpenAI:
    """Create a ChatOpenAI model instance."""
    return ChatOpenAI(
        model=model_name,
        api_key=os.getenv("FIREWORKS_API_KEY"),
        base_url="https://api.fireworks.ai/inference/v1",
        temperature=0.7,
    )


def create_analyzer_agent(model_name: str = "accounts/fireworks/models/glm-5") -> Any:
    """Create analyzer sub-agent."""
    from deepagents import create_deep_agent

    model = _create_model(model_name)

    return create_deep_agent(
        model=model,
        tools=[],  # Read-only, uses built-in tools
        system_prompt=ANALYZER_PROMPT,
    )


def create_generator_agent(model_name: str = "accounts/fireworks/models/glm-5") -> Any:
    """Create generator sub-agent."""
    from deepagents import create_deep_agent

    model = _create_model(model_name)

    return create_deep_agent(
        model=model,
        tools=WP_TOOLS,  # Has write access
        system_prompt=GENERATOR_PROMPT,
    )


def create_acf_agent(model_name: str = "accounts/fireworks/models/glm-5") -> Any:
    """Create ACF designer sub-agent."""
    from deepagents import create_deep_agent

    model = _create_model(model_name)

    return create_deep_agent(
        model=model,
        tools=WP_TOOLS,
        system_prompt=ACF_DESIGNER_PROMPT,
    )


def create_validator_agent(model_name: str = "accounts/fireworks/models/glm-5") -> Any:
    """Create validator sub-agent."""
    from deepagents import create_deep_agent

    model = _create_model(model_name)

    return create_deep_agent(
        model=model,
        tools=WP_TOOLS,
        system_prompt=VALIDATOR_PROMPT,
    )


__all__ = [
    "create_analyzer_agent",
    "create_generator_agent",
    "create_acf_agent",
    "create_validator_agent",
    "ANALYZER_PROMPT",
    "GENERATOR_PROMPT",
    "ACF_DESIGNER_PROMPT",
    "VALIDATOR_PROMPT",
]
