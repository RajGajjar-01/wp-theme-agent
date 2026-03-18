from pydantic import BaseModel, Field


class ColorPalette(BaseModel):
    primary: str = "#000000"
    secondary: str = "#333333"
    background: str = "#ffffff"
    text: str = "#333333"
    accent: str = "#0066cc"


class FontPair(BaseModel):
    heading: str | None = None
    body: str | None = None


class RepeatingComponent(BaseModel):
    name: str
    found_in: list[str]
    template_part: str
    description: str


class GlobalAnalysis(BaseModel):
    shared_header_html: str = ""
    shared_footer_html: str = ""
    shared_nav_items: list[dict[str, str]] = Field(default_factory=list)
    colors: ColorPalette = Field(default_factory=ColorPalette)
    fonts: FontPair = Field(default_factory=FontPair)
    js_libraries: list[str] = Field(default_factory=list)
    css_files: list[str] = Field(default_factory=list)
    js_files: list[str] = Field(default_factory=list)
    responsive: bool = True
    summary: str = ""
    repeating_components: list[RepeatingComponent] = Field(default_factory=list)


class PageSection(BaseModel):
    name: str
    template_part: str | None = None


class PageAnalysis(BaseModel):
    source_file: str
    page_type: str              # homepage | static_page | blog_listing | single_post | error_page | search_page | archive
    wp_template: str            # front-page.php | page-about.php | index.php | single.php | 404.php ...
    wp_page_slug: str | None = None
    title: str = ""
    sections: list[PageSection] = Field(default_factory=list)
    has_sidebar: bool = False
    has_contact_form: bool = False
    has_gallery: bool = False
    has_blog_preview: bool = False


class PlanItem(BaseModel):
    file: str                   # relative path in theme, e.g. "template-parts/hero.php"
    source: str                 # which HTML file or "global" | "css_files" | "generated" | "pages"
    type: str                   # php | css | js | xml
    description: str = ""


class ValidationResult(BaseModel):
    passed: bool
    attempts: int = 1
    error: str | None = None


class DeployStatus(BaseModel):
    method: str = "none"        # none | zip | skipped | rest_api
    success: bool = False
    message: str = ""
    url: str | None = None
