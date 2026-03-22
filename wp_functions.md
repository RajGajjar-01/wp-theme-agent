# WordPress Dynamic Element Integration Methods

When converting static HTML to WordPress, the primary challenge is preserving the original HTML structure and CSS classes while utilizing WordPress's dynamic functions.

## 1. Navigation Menus (`wp_nav_menu`)
By default, WordPress generates its own list items (`<li class="menu-item">`) and links. To map custom classes without building a complex `Walker_Nav_Menu`, use these filters in `functions.php`:

### Adding Classes to `<li>` Elements
```php
function custom_nav_li_class($classes, $item, $args) {
    if(isset($args->add_li_class)) {
        $classes[] = $args->add_li_class;
    }
    return $classes;
}
add_filter('nav_menu_css_class', 'custom_nav_li_class', 1, 3);
```

### Adding Classes to `<a>` Elements
```php
function custom_nav_a_class($atts, $item, $args) {
    if(isset($args->add_a_class)) {
        $atts['class'] = $args->add_a_class;
    }
    return $atts;
}
add_filter('nav_menu_link_attributes', 'custom_nav_a_class', 1, 3);
```

**Usage in Template (`header.php`):**
```php
wp_nav_menu(array(
    'theme_location' => 'menu-1',
    'container' => false, // Remove outer div
    'menu_class' => 'original-ul-class',
    'add_li_class' => 'original-li-class',
    'add_a_class' => 'original-a-class'
));
```

## 2. Dynamic Sidebars (Widgets)
When wrapping widgets in HTML, you can specify exactly what tags and classes HTML is rendered before and after each widget.

**Registering the Sidebar (`functions.php`):**
```php
register_sidebar( array(
    'name'          => __( 'Footer Column 1', 'theme-slug' ),
    'id'            => 'footer-1',
    'before_widget' => '<div id="%1$s" class="footer-widget %2$s">',
    'after_widget'  => '</div>',
    'before_title'  => '<h4 class="footer-widget-title">',
    'after_title'   => '</h4>',
) );
```

**Displaying the Sidebar (`footer.php`):**
```php
if ( is_active_sidebar( 'footer-1' ) ) {
    dynamic_sidebar( 'footer-1' );
}
```

## 3. Post Classes (`post_class`)
To attach custom styling classes to the WordPress loop elements dynamically:
```php
// In a loop template
<article id="post-<?php the_ID(); ?>" <?php post_class('my-custom-blog-card-class'); ?>>
```

## 4. Custom Logo (`get_custom_logo`)
WordPress outputs a hardcoded `<a>` and `<img>` tag for the logo. To add a custom class (e.g., `navbar-brand`), simply filter the output in `functions.php`:

```php
add_filter( 'get_custom_logo', 'change_logo_class' );
function change_logo_class( $html ) {
    $html = str_replace( 'custom-logo-link', 'original-logo-class', $html );
    $html = str_replace( 'custom-logo', 'original-img-class', $html );
    return $html;
}
```
