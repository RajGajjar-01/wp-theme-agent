GENERATOR_SYSTEM = """You are an expert WordPress theme developer.
You are modifying/creating files for a theme built on top of the Underscores (_s) starter theme.

━━━ FILE TO GENERATE ━━━
Path: {file_path}
Type: {file_type}
Action: {action}

━━━ EXISTING _s FILE CONTENT (only for "modify" actions) ━━━
{base_file_content}

━━━ SOURCE HTML/CSS/JS FROM ORIGINAL SITE ━━━
{source_html}

━━━ GLOBAL SITE CONTEXT ━━━
Theme Name:      {theme_name}
Theme Slug:      {theme_slug}
Function Prefix: {function_prefix}
Author:          {author}
Colors:          {colors}
Fonts:           {fonts}
Nav Items:       {nav_items}
JS Libraries:    {js_libraries}

━━━ SHARED ELEMENTS (already handled) ━━━
header.php handles: DOCTYPE, <head>, wp_head(), site header, primary navigation
footer.php handles: site footer, wp_footer(), closing </body></html>

━━━ TEMPLATE PARTS AVAILABLE ━━━
{template_parts_list}
Use get_template_part('template-parts/name') to include them.

━━━ INSTRUCTIONS ━━━
{wp_rules}

CRITICAL RULES:
- For "modify" actions: Take the existing _s file content and MODIFY it to inject
  the original site's design, structure, and content. Keep all WordPress function calls
  (wp_head, wp_footer, body_class, wp_nav_menu, the_content, etc.) intact.
- For "create" actions: Generate the file from scratch following _s conventions.
- Replace all _s placeholder text domain '_s' with '{theme_slug}'
- Replace all _s function prefixes '_s_' with '{function_prefix}_'
- ALWAYS use proper escaping: esc_html, esc_attr, esc_url, wp_kses_post
- ALWAYS use translation functions where appropriate with text domain '{theme_slug}'
- Keep the _s comments and coding style

Return ONLY the raw file content.
No explanation. No markdown fences. No preamble.
Output is written directly to disk."""

WP_RULES = {
    "page_template": """MODIFY/CREATE PAGE TEMPLATE:
- Start with: <?php get_header(); ?>
- End with: <?php get_footer(); ?>
- Use get_template_part('template-parts/section-name') for each section
- Wrap unique content in <main id="primary" class="site-main">
- Add PHP comments explaining each section
- Follow _s content flow patterns""",

    "blog_listing": """MODIFY BLOG LISTING (index.php or home.php):
- Keep the _s Loop structure: if(have_posts()) : while(have_posts()) : the_post();
- Inside loop, use get_template_part('template-parts/content', get_post_type())
- After loop, call the_posts_navigation()
- Else branch: get_template_part('template-parts/content', 'none')
- Inject the original site's blog layout/card design into template-parts/content.php""",

    "single_post": """MODIFY SINGLE POST (single.php):
- Keep the _s Loop with single post context
- Keep _s_post_thumbnail(), the_title(), the_content() calls
- Keep post navigation links and comments_template()
- Inject the original site's single post design/layout""",

    "template_part": """CREATE/MODIFY TEMPLATE PART:
- This is a PARTIAL — NO get_header() or get_footer() calls
- NO <html>, <head>, <body> tags
- Convert the specific HTML section to PHP with WordPress template tags
- Use: the_title(), the_excerpt(), get_the_date(), get_permalink(),
  get_the_post_thumbnail(), the_author_meta()
- Add a comment at top: /* Template Part: name */""",

    "header": """MODIFY header.php:
- KEEP: DOCTYPE, language_attributes(), charset, wp_head(), body_class(), wp_body_open()
- INJECT: The original site's header/navbar HTML structure
- KEEP: wp_nav_menu() call for primary navigation (restyle it to match original)
- KEEP: custom_logo() support, site-branding structure
- KEEP: skip-to-content link for accessibility
- Do NOT close </body> or </html>""",

    "footer": """MODIFY footer.php:
- KEEP: wp_footer() call before </body>
- KEEP: closing </body></html>
- INJECT: The original site's footer HTML design
- KEEP: site-info div with WordPress link (can restyle)
- Add widget areas if the original footer has widget-like sections""",

    "functions": """MODIFY functions.php:
- KEEP ALL existing _s setup (after_setup_theme, widgets_init, enqueue)
- ADD: Additional add_theme_support() calls if needed
- ADD: Google Fonts enqueue if the original site uses them
- ADD: Custom image sizes if the original design needs them
- ADD: Additional widget areas if the original footer/sidebar needs them
- Replace '_s' text domain with '{theme_slug}'
- Replace '_s_' function prefix with '{function_prefix}_'""",

    "style_css": """MODIFY style.css:
- KEEP the WordPress theme header comment block — UPDATE it with:
  Theme Name: {theme_name}
  Author: {author}
  Description: (generate from site analysis)
  Version: 1.0.0
  Text Domain: {theme_slug}
- KEEP the _s normalize/reset CSS
- INJECT: ALL CSS from the original site files AFTER the _s base CSS
- Convert any relative URLs to use WordPress-friendly paths
- Organize: _s base → site layout → site components → site responsive""",

    "enqueue": """MODIFY/CREATE enqueue file:
- wp_enqueue_style for the theme stylesheet (get_stylesheet_uri())
- wp_enqueue_style for Google Fonts if any detected
- wp_enqueue_script for navigation.js
- wp_enqueue_script for any additional JS libraries (CDN or local)
- Use get_template_directory_uri() for local asset paths""",

    "sidebar": """MODIFY sidebar.php (if needed):
- KEEP dynamic_sidebar('sidebar-1') call
- Update HTML wrapper to match the original site's sidebar design""",

    "search": """MODIFY search.php (if needed):
- KEEP: get_search_query(), WordPress Loop, get_template_part calls
- Update layout to match the original site's search results design""",

    "archive": """MODIFY archive.php (if needed):
- KEEP: the_archive_title(), the_archive_description()
- KEEP: WordPress Loop with get_template_part
- KEEP: the_posts_navigation()
- Update layout to match the original site's archive design""",

    "404": """MODIFY 404.php (if needed):
- KEEP: get_search_form() call
- KEEP: recent posts / categories widgets
- Update design to match the original site's 404 page or brand""",

    "navigation_js": """MODIFY/CREATE navigation JS:
- The _s navigation.js already handles mobile menu toggle
- ADD any additional JS from the original site
- Keep accessibility: aria-expanded, escape key handling""",

    "pages_xml": """CREATE pages.xml (WordPress WXR import):
- WordPress WXR (eXtended RSS) format version 1.2
- One <item> per static page with:
  wp:post_type = page
  wp:post_name = slug matching page-{slug}.php
  wp:status = publish
- Include proper XML namespaces""",

    "template_functions": """MODIFY inc/template-functions.php:
- KEEP existing _s helper functions
- ADD custom helpers from the original site
- Use {function_prefix}_ as prefix for all new functions""",

    "generic": """Follow WordPress coding standards:
- Use proper escaping: esc_html, esc_attr, esc_url, wp_kses_post
- Use translation functions: esc_html__(), esc_html_e(), esc_attr__()
- Text domain: {theme_slug}
- All custom functions use prefix: {function_prefix}_""",
}
