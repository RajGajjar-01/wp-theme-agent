<?php
/**
 * The template for displaying the footer
 *
 * Contains the closing of the #content div and all content after.
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package asdfafa
 */

?>

	<!-- ========== FOOTER ========== -->
	<footer class="footer">
		<div class="container">
			<div class="footer-top">
				<div class="footer-brand">
					<div class="nav-logo">
						<i class="fa-solid fa-droplet"></i>
						<span><?php echo esc_html( get_bloginfo( 'name' ) ?: 'FlowForce' ); ?></span>
					</div>
					<p><?php echo esc_html( get_field( 'footer_description', 'option' ) ?: 'Professional Plumbing & HVAC services you can count on — 24 hours a day, 365 days a year.' ); ?></p>
					<div class="social-links">
						<?php if ( $facebook = get_field( 'facebook_url', 'option' ) ) : ?>
							<a href="<?php echo esc_url( $facebook ); ?>" target="_blank" rel="noopener"><i class="fa-brands fa-facebook-f"></i></a>
						<?php endif; ?>
						<?php if ( $instagram = get_field( 'instagram_url', 'option' ) ) : ?>
							<a href="<?php echo esc_url( $instagram ); ?>" target="_blank" rel="noopener"><i class="fa-brands fa-instagram"></i></a>
						<?php endif; ?>
						<?php if ( $twitter = get_field( 'twitter_url', 'option' ) ) : ?>
							<a href="<?php echo esc_url( $twitter ); ?>" target="_blank" rel="noopener"><i class="fa-brands fa-x-twitter"></i></a>
						<?php endif; ?>
						<?php if ( $yelp = get_field( 'yelp_url', 'option' ) ) : ?>
							<a href="<?php echo esc_url( $yelp ); ?>" target="_blank" rel="noopener"><i class="fa-brands fa-yelp"></i></a>
						<?php endif; ?>
					</div>
				</div>
				<div class="footer-col">
					<h4><?php esc_html_e( 'Services', 'asdfafa' ); ?></h4>
					<ul>
						<li><a href="#services"><?php esc_html_e( 'Heating Systems', 'asdfafa' ); ?></a></li>
						<li><a href="#services"><?php esc_html_e( 'Air Conditioning', 'asdfafa' ); ?></a></li>
						<li><a href="#services"><?php esc_html_e( 'Plumbing Repair', 'asdfafa' ); ?></a></li>
						<li><a href="#services"><?php esc_html_e( 'Water Heaters', 'asdfafa' ); ?></a></li>
						<li><a href="#services"><?php esc_html_e( 'Indoor Air Quality', 'asdfafa' ); ?></a></li>
						<li><a href="#services"><?php esc_html_e( 'Emergency Service', 'asdfafa' ); ?></a></li>
					</ul>
				</div>
				<div class="footer-col">
					<h4><?php esc_html_e( 'Company', 'asdfafa' ); ?></h4>
					<ul>
						<li><a href="#why-us"><?php esc_html_e( 'About Us', 'asdfafa' ); ?></a></li>
						<li><a href="#process"><?php esc_html_e( 'Our Process', 'asdfafa' ); ?></a></li>
						<li><a href="#testimonials"><?php esc_html_e( 'Reviews', 'asdfafa' ); ?></a></li>
						<li><a href="#contact"><?php esc_html_e( 'Get an Estimate', 'asdfafa' ); ?></a></li>
					</ul>
				</div>
				<div class="footer-col">
					<h4><?php esc_html_e( 'Contact', 'asdfafa' ); ?></h4>
					<ul>
						<?php $phone = get_field( 'phone_number', 'option' ); ?>
						<li><a href="tel:<?php echo esc_attr( $phone ?: '+18005551234' ); ?>"><?php echo esc_html( $phone ?: '+1 (800) 555-1234' ); ?></a></li>
						<?php $email = get_field( 'email_address', 'option' ); ?>
						<li><a href="mailto:<?php echo esc_attr( $email ?: 'hello@flowforce.com' ); ?>"><?php echo esc_html( $email ?: 'hello@flowforce.com' ); ?></a></li>
						<li><?php esc_html_e( 'Mon–Sat: 7am – 8pm', 'asdfafa' ); ?></li>
						<li><?php esc_html_e( 'Emergency: 24/7', 'asdfafa' ); ?></li>
					</ul>
				</div>
			</div>
			<div class="footer-bottom">
				<p>&copy; <?php echo date( 'Y' ); ?> <?php echo esc_html( get_bloginfo( 'name' ) ); ?> <?php esc_html_e( 'Plumbing & HVAC. All rights reserved.', 'asdfafa' ); ?></p>
				<p><?php echo esc_html( get_field( 'license_info', 'option' ) ?: 'Licensed, Bonded & Insured — LIC #PH-44821' ); ?></p>
			</div>
		</div>
	</footer>

	<!-- ========== BACK TO TOP ========== -->
	<button class="back-to-top" id="backToTop">
		<i class="fa-solid fa-chevron-up"></i>
	</button>

</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>