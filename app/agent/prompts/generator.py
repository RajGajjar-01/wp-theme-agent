GENERATOR_SYSTEM = """You are an expert WordPress theme developer.
Generate ONLY the content of: {file_path}
File type: {file_type}

━━━ SOURCE HTML FOR THIS FILE ━━━
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

━━━ SHARED ELEMENTS (already handled — DO NOT repeat) ━━━
header.php handles: opening DOCTYPE, <head>, wp_head(), site header, primary navigation
footer.php handles: site footer, wp_footer(), closing </body></html>

━━━ TEMPLATE PARTS AVAILABLE ━━━
{template_parts_list}
Use get_template_part('template-parts/name') to include them.

━━━ WORDPRESS RULES FOR THIS FILE ━━━
{wp_rules}

Return ONLY the raw file content.
No explanation. No markdown fences. No preamble.
Output is written directly to disk."""

WP_RULES = {
    "page_template": """- Start with: <?php get_header(); ?>
- End with: <?php get_footer(); ?>
- Use get_template_part('template-parts/section-name') for each section
- Wrap unique content in <main id="main" class="site-main">
- Add PHP comments explaining each section""",

    "blog_listing": """- Start with: <?php get_header(); ?>
- Use WordPress Loop: if(have_posts()) : while(have_posts()) : the_post();
- Inside loop, use get_template_part('template-parts/cards/post') for each post
- After loop, call the_posts_navigation()
- Else branch: get_template_part('template-parts/content', 'none')
- End with: <?php get_footer(); ?>""",

    "single_post": """- Start with: <?php get_header(); ?>
- WordPress Loop with single post context
- Use the_title(), the_content(), the_author_meta(), get_avatar()
- Use previous_post_link() and next_post_link() for post navigation
- Include comments_template() at the bottom
- End with: <?php get_footer(); ?>""",

    "template_part": """- This is a PARTIAL — NO get_header() or get_footer() calls
- NO <html>, <head>, <body> tags
- Just the specific HTML section converted to PHP
- Use WordPress template tags: the_title(), the_excerpt(), get_the_date(),
  get_permalink(), get_the_post_thumbnail(), the_author_meta()
- Add a comment at top: /* Template Part: name — description */""",

    "header": """- Full DOCTYPE, <html <?php language_attributes(); ?>>
- <head> block with wp_head() as LAST item before </head>
- Opening <body <?php body_class(); ?>>
- wp_body_open() right after <body>
- Site branding with custom_logo support
- Nav: wp_nav_menu(['theme_location' => 'primary', 'container' => 'nav'])
- Do NOT close </body> or </html> — that is footer.php's job""",

    "footer": """- Close any wrapping divs opened in header.php
- Footer HTML content from original site
- Widget areas if applicable
- wp_footer() as LAST item before </body>
- Closing </body></html>""",

    "functions": """- Theme setup via after_setup_theme hook
- add_theme_support for: title-tag, post-thumbnails, html5, custom-logo, customize-selective-refresh-widgets
- register_nav_menus: primary + footer menus
- require inc/enqueue.php and inc/template-functions.php
- widgets_init hook to register sidebar
- Use {function_prefix}_ as prefix for all functions
- load_theme_textdomain for i18n""",

    "style_css": """- WordPress theme header comment block is REQUIRED:
  /*
  Theme Name: {theme_name}
  Author: {author}
  Description: ...
  Version: 1.0.0
  Text Domain: {theme_slug}
  */
- Then include ALL CSS from the original site files
- Convert any relative URLs (images, fonts) to use WordPress paths
- Add any responsive/reset CSS needed""",

    "enqueue": """- Use wp_enqueue_scripts hook
- wp_enqueue_style for the theme stylesheet (get_stylesheet_uri())
- wp_enqueue_style for Google Fonts if any
- wp_enqueue_script for navigation.js with array('jquery') dependency
- wp_enqueue_script for any JS libraries detected (CDN or local)
- Use get_template_directory_uri() for local asset paths""",

    "sidebar": """- Simple sidebar template
- Use dynamic_sidebar('sidebar-1')
- Wrap in appropriate HTML with widget area check""",

    "search": """- Start with: <?php get_header(); ?>
- Show search results heading with get_search_query()
- WordPress Loop for results
- Use get_template_part('template-parts/cards/post') for each result
- Show "no results" message if no posts found
- End with: <?php get_footer(); ?>""",

    "archive": """- Start with: <?php get_header(); ?>
- Show archive title with the_archive_title() and the_archive_description()
- WordPress Loop for posts
- Use get_template_part('template-parts/cards/post') for each post
- Include the_posts_navigation()
- End with: <?php get_footer(); ?>""",

    "404": """- Start with: <?php get_header(); ?>
- Show a 404 error message
- Include a search form with get_search_form()
- Optionally show recent posts or categories
- End with: <?php get_footer(); ?>""",

    "navigation_js": """- Pure JavaScript (no jQuery dependency required)
- Toggle mobile navigation menu visibility
- Handle aria-expanded attribute for accessibility
- Close menu when clicking outside
- Handle escape key to close menu""",

    "pages_xml": """- WordPress WXR (eXtended RSS) format version 1.2
- One <item> per static page with:
  wp:post_type = page
  wp:post_name = slug matching page-{slug}.php
  wp:status = publish
- Include proper XML namespaces""",

    "template_functions": """- Helper functions used by template files
- Custom excerpt length/more text functions
- Breadcrumb helper if needed
- Any utility functions for the theme
- Use {function_prefix}_ as prefix for all functions""",

    "generic": """- Follow WordPress coding standards
- Use proper escaping: esc_html, esc_attr, esc_url, wp_kses_post
- Use translation functions: esc_html__(), esc_html_e(), esc_attr__()
- Text domain: {theme_slug}""",
}
