<?php
/**
 * The header for our theme
 *
 * This is the template that displays all of the <head> section and everything up until <div id="content">
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package asdfafa
 */

?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">

	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

	<!-- ========== LOADER ========== -->
	<div class="loader" id="loader">
		<div class="loader-icon">
			<i class="fa-solid fa-droplet"></i>
		</div>
		<span><?php echo esc_html( get_bloginfo( 'name' ) ?: 'FlowForce' ); ?></span>
	</div>

	<!-- ========== NAVBAR ========== -->
	<nav class="navbar" id="navbar">
		<div class="nav-logo">
			<i class="fa-solid fa-droplet"></i>
			<span><?php echo esc_html( get_bloginfo( 'name' ) ?: 'FlowForce' ); ?></span>
		</div>
		<?php
		wp_nav_menu(
			array(
				'theme_location' => 'menu-1',
				'menu_id'        => 'navLinks',
				'menu_class'     => 'nav-links',
				'container'      => '',
				'add_li_class'   => '',
				'add_a_class'    => '',
			)
		);
		?>
		<?php $phone = get_field( 'phone_number', 'option' ); ?>
		<a href="tel:<?php echo esc_attr( $phone ?: '+18005551234' ); ?>" class="nav-cta">
			<i class="fa-solid fa-phone"></i> <?php esc_html_e( 'Call Now', 'asdfafa' ); ?>
		</a>
		<div class="hamburger" id="hamburger">
			<span></span><span></span><span></span>
		</div>
	</nav>

<div id="page" class="site">
	<a class="skip-link screen-reader-text" href="#primary"><?php esc_html_e( 'Skip to content', 'asdfafa' ); ?></a>