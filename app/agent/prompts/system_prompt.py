import re


def build_system_prompt(
    uploaded_files: dict[str, str],
    theme_name: str,
    theme_slug: str,
    author: str,
    base_theme_files: list[dict],
) -> str:
    """
    Build a concise system prompt for the WordPress theme conversion agent.
    """

    func_prefix = theme_slug.replace("-", "_")

    # Build uploaded file listing (compact)
    upload_listing = ", ".join(
        f"{name} ({len(content)} chars)" for name, content in uploaded_files.items()
    )

    # Categorize uploaded files
    html_files = [n for n in uploaded_files if n.endswith((".html", ".htm"))]
    css_files = [n for n in uploaded_files if n.endswith(".css")]
    js_files = [n for n in uploaded_files if n.endswith(".js")]

    # Compact base theme listing — just filenames, no sizes
    base_listing = ", ".join(f["path"] for f in base_theme_files)

    # Analyze HTML content for SPA-style multi-page detection
    spa_pages = []
    for name, content in uploaded_files.items():
        if name.endswith((".html", ".htm")):
            main_matches = re.findall(
                r'<main[^>]*id=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*page[^"\']*["\']',
                content,
            )
            if len(main_matches) > 1:
                spa_pages = main_matches
                break
            if not spa_pages:
                section_matches = re.findall(
                    r'<(?:section|div)[^>]*id=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*page[^"\']*["\']',
                    content,
                )
                if len(section_matches) > 1:
                    spa_pages = section_matches
                    break

    # Page analysis section — kept concise
    if spa_pages:
        page_section = f"""
## SPA Multi-Page ({len(spa_pages)} sections detected)
Page IDs: {", ".join(spa_pages)}

Extract each <main id="page-id"> into a SEPARATE PHP template:
- "{spa_pages[0]}" → front-page.php
- Other IDs → page-{{slug}}.php (with Template Name header)

Each template: `get_header()` → section content only (no <main> wrapper) → `get_footer()`
Custom templates need: `<?php /* Template Name: Page Name */ ?>`
"""
    elif len(html_files) > 1:
        page_section = f"""
## Multi-Page ({len(html_files)} HTML pages): {", ".join(html_files)}

Mapping: index/home.html → front-page.php | about.html → page-about.php | blog.html → home.php | others → page-{{slug}}.php
Custom templates need: `<?php /* Template Name: Page Name */ ?>`
"""
    elif len(html_files) == 1:
        page_section = f"""
## Single-Page: {html_files[0]} → front-page.php
Preserve ALL sections.
"""
    else:
        page_section = ""

    return f"""You are a WordPress theme conversion agent. Convert uploaded website files into a WordPress theme by MODIFYING the pre-seeded _s (Underscores) base theme.

## Theme: {theme_name}
Slug: {theme_slug} | Text Domain: {theme_slug} | Prefix: {func_prefix}_ | Author: {author}

## Uploaded Files
{upload_listing}
HTML: {", ".join(html_files) or "None"} | CSS: {", ".join(css_files) or "None"} | JS: {", ".join(js_files) or "None"}

## Base Theme (pre-seeded in {theme_slug}/)
{base_listing}
All _s → {theme_slug} replacements done.
{page_section}
## Workflow
1. **Analyze**: Read ALL uploaded files. Identify layout, colors, fonts, sections, navigation, CDN deps.
2. **Header/Footer**: Modify {theme_slug}/header.php and footer.php. Use copy_section or edit_file. Lint both.
3. **Styles/Scripts**: Append uploaded CSS to style.css (use copy_section mode='append'). Copy JS to js/. Update functions.php to enqueue Google Fonts, icon CDNs, theme CSS/JS.
4. **Templates**: Create front-page.php and page templates. Use generate_acf_fields() for editable content, then use `get_field('name') ?: 'fallback'` pattern. Lint every PHP file.
5. **Finalize**: Lint all PHP. Call task_complete.

## Rules

**Output**: Only .php, .css, .js, .json files. Never .html. Every template: `get_header()` content `get_footer()`.

**Visibility**: Fix `opacity:0` / `visibility:hidden` reveal animations — set default to `opacity:1` so content shows even if JS fails.

**Structure**: header.php opens tags (e.g. `<div id="page">`), footer.php closes them. They MUST match.

**Dependencies**: NEVER hardcode `<link>`/`<script>` in templates. Always `wp_enqueue_style()`/`wp_enqueue_script()` in functions.php. Use `get_template_directory_uri()` for assets.

**Navigation**: Use `wp_nav_menu()` with filters for custom classes:
```php
// In functions.php — add custom li/a classes
function {func_prefix}_nav_li_class($classes, $item, $args) {{
    if(isset($args->add_li_class)) {{ $classes[] = $args->add_li_class; }}
    return $classes;
}}
add_filter('nav_menu_css_class', '{func_prefix}_nav_li_class', 1, 3);
function {func_prefix}_nav_a_class($atts, $item, $args) {{
    if(isset($args->add_a_class)) {{ $atts['class'] = $args->add_a_class; }}
    return $atts;
}}
add_filter('nav_menu_link_attributes', '{func_prefix}_nav_a_class', 1, 3);
```

**CSS**: Keep WP theme header. Include ALL uploaded CSS — never skip/truncate. Use copy_section for large CSS.

**Escaping**: Strings: `esc_html_e()` | Attributes: `esc_attr_e()` | URLs: `esc_url()` | Text domain: '{theme_slug}'

**No empty files**: Every template must have real content between header/footer.

**No duplicate <body>**: header.php has the body tag. Page templates start with section content. Use `body_class` filter for page-specific classes.

**Token efficiency**: Prefer edit_file for small changes. Use copy_section/copy_file over write_file for large content. Use search_in_file/grep_workspace to find code locations.

**ACF — EVERY piece of content must be editable**: Use generate_acf_fields() tool — it handles ALL wiring automatically.
- NEVER manually write ACF JSON files, `acf_add_local_field_group()` code, or `acf/settings` filters — the tool does this.
- For site-wide fields (social links, footer text), use `scope: "global"` — the tool auto-registers the Theme Options page.
- NEVER use `esc_html_e('Hardcoded text')` for page content. Only use it for UI labels like "Email:" or "Phone:".
- ALL text, images, links, and buttons in templates MUST use `get_field()` with a fallback.

**Repeating content (features, services, team, testimonials, pricing, etc.) MUST use ACF repeater fields:**
- Use type `"repeater"` with `"sub_fields"` in generate_acf_fields()
- In templates, loop with `have_rows()`/`the_row()`:
```php
<?php if( have_rows('services') ): while( have_rows('services') ): the_row(); ?>
  <div class="service-card">
    <h3><?php echo esc_html(get_sub_field('title') ?: 'Service'); ?></h3>
    <p><?php echo esc_html(get_sub_field('description') ?: 'Description'); ?></p>
  </div>
<?php endwhile; endif; ?>
```
- Template field patterns:
  - Single text: `<?php echo esc_html(get_field('field') ?: 'Default'); ?>`
  - Image: `<?php $img = get_field('hero_bg'); if($img): ?><img src="<?php echo esc_url($img); ?>"><?php endif; ?>`
  - Global field: `<?php echo esc_html(get_field('field', 'option') ?: 'Default'); ?>`

## Enqueue Pattern
```php
function {func_prefix}_scripts() {{
    wp_enqueue_style('{theme_slug}-google-fonts', 'https://fonts.googleapis.com/...', array(), null);
    wp_enqueue_style('font-awesome', 'https://cdnjs.cloudflare.com/...', array(), '6.5.0');
    wp_enqueue_style('{theme_slug}-style', get_stylesheet_uri(), array('{theme_slug}-google-fonts', 'font-awesome'), {func_prefix.upper()}_VERSION);
    wp_enqueue_script('{theme_slug}-theme', get_template_directory_uri() . '/js/theme.js', array(), {func_prefix.upper()}_VERSION, true);
}}
add_action('wp_enqueue_scripts', '{func_prefix}_scripts');
```
"""
