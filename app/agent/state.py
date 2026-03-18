from typing import TypedDict

from app.agent.models import (
    DeployStatus,
    GlobalAnalysis,
    PageAnalysis,
    PlanItem,
    ValidationResult,
)


class AgentState(TypedDict):
    # Input
    session_id: str
    theme_name: str
    theme_slug: str
    author: str

    # Uploaded raw files
    uploaded_files: dict[str, str]           # filename → raw content

    # Multi-page analysis (two-level)
    global_analysis: GlobalAnalysis          # shared header, footer, nav, colors, fonts, components
    pages: list[PageAnalysis]                # per-page: source_file, page_type, wp_template, sections

    # Planner output
    plan: list[PlanItem]                     # ordered list of files to generate

    # Generator output
    generated_files: dict[str, str]          # wp_filename → generated content

    # Validator output
    validation_results: dict[str, ValidationResult]

    # Writer output
    written_files: list[str]
    zip_path: str
    pages_xml: str                           # WXR import file content
    deploy_status: DeployStatus

    # Error tracking
    errors: list[str]

    # LangChain message history
    messages: list
