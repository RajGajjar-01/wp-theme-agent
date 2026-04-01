<?php
/**
 * The front page template file.
 *
 * @package asdfafa
 */

get_header();
?>

	<main id="primary" class="site-main">

		<!-- ========== HERO ========== -->
		<section class="hero" id="home">
			<div class="hero-bg-grid"></div>
			<div class="hero-content">
				<div class="hero-badge reveal">
					<span class="pulse-dot"></span> <?php echo esc_html( get_field( 'hero_badge_text' ) ?: 'Available 24/7 — Emergency Service' ); ?>
				</div>
				<h1 class="reveal">
					<?php echo esc_html( get_field( 'hero_headline_1' ) ?: 'Your Home.' ); ?><br/>
					<span class="accent"><?php echo esc_html( get_field( 'hero_headline_accent' ) ?: 'Perfectly' ); ?></span><br/>
					<?php echo esc_html( get_field( 'hero_headline_2' ) ?: 'Flowing.' ); ?>
				</h1>
				<p class="hero-sub reveal"><?php echo esc_html( get_field( 'hero_subheadline' ) ?: 'Expert Plumbing & HVAC solutions delivered fast, clean, and guaranteed. Serving families since 1998.' ); ?></p>
				<div class="hero-actions reveal">
					<a href="<?php echo esc_url( get_field( 'hero_btn_primary_link' ) ?: '#contact' ); ?>" class="btn btn-primary"><?php echo esc_html( get_field( 'hero_btn_primary_text' ) ?: 'Get Free Estimate' ); ?></a>
					<a href="<?php echo esc_url( get_field( 'hero_btn_secondary_link' ) ?: '#services' ); ?>" class="btn btn-ghost"><?php echo esc_html( get_field( 'hero_btn_secondary_text' ) ?: 'Explore Services' ); ?></a>
				</div>
				<div class="hero-stats reveal">
					<div class="stat">
						<strong><?php echo esc_html( get_field( 'hero_stat_1_value' ) ?: '25+' ); ?></strong><span><?php echo esc_html( get_field( 'hero_stat_1_label' ) ?: 'Years Experience' ); ?></span>
					</div>
					<div class="stat-divider"></div>
					<div class="stat">
						<strong><?php echo esc_html( get_field( 'hero_stat_2_value' ) ?: '12K+' ); ?></strong><span><?php echo esc_html( get_field( 'hero_stat_2_label' ) ?: 'Jobs Completed' ); ?></span>
					</div>
					<div class="stat-divider"></div>
					<div class="stat">
						<strong><?php echo esc_html( get_field( 'hero_stat_3_value' ) ?: '100%' ); ?></strong><span><?php echo esc_html( get_field( 'hero_stat_3_label' ) ?: 'Satisfaction Rate' ); ?></span>
					</div>
				</div>
			</div>
			<div class="hero-visual reveal">
				<div class="hero-card card-1">
					<i class="<?php echo esc_attr( get_field( 'hero_card_1_icon' ) ?: 'fa-solid fa-temperature-half' ); ?>"></i>
					<div>
						<strong><?php echo esc_html( get_field( 'hero_card_1_title' ) ?: 'AC Repair' ); ?></strong>
						<span><?php echo esc_html( get_field( 'hero_card_1_subtitle' ) ?: 'Same-day service' ); ?></span>
					</div>
				</div>
				<div class="hero-card card-2">
					<i class="<?php echo esc_attr( get_field( 'hero_card_2_icon' ) ?: 'fa-solid fa-wrench' ); ?>"></i>
					<div>
						<strong><?php echo esc_html( get_field( 'hero_card_2_title' ) ?: 'Pipe Fix' ); ?></strong>
						<span><?php echo esc_html( get_field( 'hero_card_2_subtitle' ) ?: 'No mess, no stress' ); ?></span>
					</div>
				</div>
				<div class="hero-image-wrap">
					<?php 
					$hero_image = get_field( 'hero_image' );
					if ( $hero_image ) : ?>
						<img src="<?php echo esc_url( $hero_image ); ?>" alt="<?php esc_attr_e( 'Technician at work', 'asdfafa' ); ?>"/>
					<?php else : ?>
						<img src="https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=600&q=80" alt="<?php esc_attr_e( 'Technician at work', 'asdfafa' ); ?>"/>
					<?php endif; ?>
					<div class="hero-image-badge">
						<i class="fa-solid fa-shield-halved"></i>
						<span><?php esc_html_e( 'Licensed & Insured', 'asdfafa' ); ?></span>
					</div>
				</div>
			</div>
			<div class="scroll-hint">
				<span><?php esc_html_e( 'Scroll', 'asdfafa' ); ?></span>
				<i class="fa-solid fa-arrow-down"></i>
			</div>
		</section>

		<!-- ========== SERVICES ========== -->
		<section class="services section" id="services">
			<div class="container">
				<div class="section-header reveal">
					<span class="label"><?php echo esc_html( get_field( 'services_label' ) ?: 'What We Do' ); ?></span>
					<h2><?php echo esc_html( get_field( 'services_title' ) ?: 'Our Core Services' ); ?></h2>
					<p><?php echo esc_html( get_field( 'services_description' ) ?: 'From leaky faucets to full HVAC system installations — we handle it all with precision.' ); ?></p>
				</div>
				<div class="services-grid">
					<?php 
					$delay = 0;
					if ( have_rows( 'services' ) ) :
						while ( have_rows( 'services' ) ) : the_row();
							$icon_class = get_sub_field( 'icon_class' ) ?: 'fa-solid fa-wrench';
							$icon_color = get_sub_field( 'icon_color' ) ?: '#2196F3';
							$title = get_sub_field( 'title' ) ?: 'Service';
							$description = get_sub_field( 'description' ) ?: 'Description';
							$features = get_sub_field( 'features' );
							$is_emergency = get_sub_field( 'is_emergency' );
							$features_list = $features ? explode( "\n", $features ) : array();
							?>
							<div class="service-card reveal<?php echo $is_emergency ? ' emergency-card' : ''; ?>" data-delay="<?php echo esc_attr( $delay ); ?>">
								<?php if ( $is_emergency ) : ?>
									<div class="emergency-badge"><span class="pulse-dot red"></span> <?php esc_html_e( 'Emergency', 'asdfafa' ); ?></div>
								<?php endif; ?>
								<div class="service-icon" style="--c:<?php echo esc_attr( $icon_color ); ?>">
									<i class="<?php echo esc_attr( $icon_class ); ?>"></i>
								</div>
								<h3><?php echo esc_html( $title ); ?></h3>
								<p><?php echo esc_html( $description ); ?></p>
								<?php if ( ! empty( $features_list ) ) : ?>
									<ul>
										<?php foreach ( $features_list as $feature ) : ?>
											<li><?php echo esc_html( trim( $feature ) ); ?></li>
										<?php endforeach; ?>
									</ul>
								<?php endif; ?>
								<?php if ( $is_emergency ) : 
									$phone = get_field( 'phone_number', 'option' ); ?>
									<a href="tel:<?php echo esc_attr( $phone ?: '+18005551234' ); ?>" class="btn btn-emergency">
										<i class="fa-solid fa-phone-volume"></i> <?php esc_html_e( 'Call Emergency Line', 'asdfafa' ); ?>
									</a>
								<?php else : ?>
									<a href="#contact" class="service-link"><?php esc_html_e( 'Book Now', 'asdfafa' ); ?> <i class="fa-solid fa-arrow-right"></i></a>
								<?php endif; ?>
							</div>
							<?php 
							$delay += 100;
						endwhile;
					else : 
						// Default services
						$default_services = array(
							array( 'icon' => 'fa-solid fa-fire-flame-curved', 'color' => '#E8420A', 'title' => 'Heating Systems', 'desc' => 'Furnace installation, repair, and tune-ups. Stay warm all winter with our certified heating experts.', 'features' => "Furnace Repair & Replacement\nBoiler Services\nRadiant Heating" ),
							array( 'icon' => 'fa-solid fa-snowflake', 'color' => '#0A87E8', 'title' => 'Air Conditioning', 'desc' => 'Keep cool with high-efficiency AC installs, repairs, and annual maintenance plans tailored to your home.', 'features' => "AC Installation & Repair\nDuct Cleaning & Sealing\nSmart Thermostat Setup" ),
							array( 'icon' => 'fa-solid fa-faucet-drip', 'color' => '#0ABF8A', 'title' => 'Plumbing Repair', 'desc' => 'Emergency or routine — our plumbers are ready to tackle leaks, clogs, and pipe issues with speed and care.', 'features' => "Leak Detection & Repair\nDrain & Sewer Cleaning\nFixture Installation" ),
							array( 'icon' => 'fa-solid fa-water', 'color' => '#A30AE8', 'title' => 'Water Heaters', 'desc' => 'Traditional tank or energy-saving tankless — we install and repair all water heater types quickly.', 'features' => "Tank & Tankless Installation\nHot Water Repair\nAnnual Flushing Service" ),
							array( 'icon' => 'fa-solid fa-wind', 'color' => '#E8A80A', 'title' => 'Indoor Air Quality', 'desc' => 'Breathe cleaner air with our filtration, humidification, and ventilation system services.', 'features' => "Air Purifier Installation\nHumidity Control\nVentilation Solutions" ),
							array( 'icon' => 'fa-solid fa-bolt', 'color' => '#E8100A', 'title' => '24/7 Emergency', 'desc' => 'Burst pipe at midnight? Heater out in a snowstorm? We\'re always on call. Fast response guaranteed.', 'features' => '', 'emergency' => true ),
						);
						foreach ( $default_services as $i => $service ) : ?>
							<div class="service-card reveal<?php echo ! empty( $service['emergency'] ) ? ' emergency-card' : ''; ?>" data-delay="<?php echo esc_attr( $i * 100 ); ?>">
								<?php if ( ! empty( $service['emergency'] ) ) : ?>
									<div class="emergency-badge"><span class="pulse-dot red"></span> <?php esc_html_e( 'Emergency', 'asdfafa' ); ?></div>
								<?php endif; ?>
								<div class="service-icon" style="--c:<?php echo esc_attr( $service['color'] ); ?>">
									<i class="<?php echo esc_attr( $service['icon'] ); ?>"></i>
								</div>
								<h3><?php echo esc_html( $service['title'] ); ?></h3>
								<p><?php echo esc_html( $service['desc'] ); ?></p>
								<?php if ( ! empty( $service['features'] ) ) : 
									$features_list = explode( "\n", $service['features'] ); ?>
									<ul>
										<?php foreach ( $features_list as $feature ) : ?>
											<li><?php echo esc_html( trim( $feature ) ); ?></li>
										<?php endforeach; ?>
									</ul>
								<?php endif; ?>
								<?php if ( ! empty( $service['emergency'] ) ) : 
									$phone = get_field( 'phone_number', 'option' ); ?>
									<a href="tel:<?php echo esc_attr( $phone ?: '+18005551234' ); ?>" class="btn btn-emergency">
										<i class="fa-solid fa-phone-volume"></i> <?php esc_html_e( 'Call Emergency Line', 'asdfafa' ); ?>
									</a>
								<?php else : ?>
									<a href="#contact" class="service-link"><?php esc_html_e( 'Book Now', 'asdfafa' ); ?> <i class="fa-solid fa-arrow-right"></i></a>
								<?php endif; ?>
							</div>
						<?php endforeach;
					endif;
					?>
				</div>
			</div>
		</section>

		<!-- ========== WHY US ========== -->
		<section class="why-us section" id="why-us">
			<div class="container">
				<div class="why-inner">
					<div class="why-image-side reveal">
						<?php 
						$why_image = get_field( 'why_us_image' );
						if ( $why_image ) : ?>
							<img src="<?php echo esc_url( $why_image ); ?>" alt="<?php esc_attr_e( 'HVAC technician', 'asdfafa' ); ?>"/>
						<?php else : ?>
							<img src="https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=600&q=80" alt="<?php esc_attr_e( 'HVAC technician', 'asdfafa' ); ?>"/>
						<?php endif; ?>
						<div class="experience-badge">
							<strong><?php echo esc_html( get_field( 'years_in_business' ) ?: '25' ); ?></strong>
							<span><?php esc_html_e( 'Years in', 'asdfafa' ); ?><br/><?php esc_html_e( 'Business', 'asdfafa' ); ?></span>
						</div>
					</div>
					<div class="why-content-side reveal">
						<span class="label"><?php echo esc_html( get_field( 'why_us_label' ) ?: 'Why Choose Us' ); ?></span>
						<h2><?php echo esc_html( get_field( 'why_us_title' ) ?: 'Built on Trust, Backed by Expertise' ); ?></h2>
						<p><?php echo esc_html( get_field( 'why_us_description' ) ?: "We're not just another service company. FlowForce is a family-run business that treats every home like our own — with honesty, skill, and respect." ); ?></p>

						<div class="why-points">
							<?php 
							if ( have_rows( 'why_us_points' ) ) :
								while ( have_rows( 'why_us_points' ) ) : the_row();
									$icon = get_sub_field( 'icon_class' ) ?: 'fa-solid fa-certificate';
									$title = get_sub_field( 'title' ) ?: 'Feature';
									$desc = get_sub_field( 'description' ) ?: 'Description';
									?>
									<div class="why-point">
										<div class="why-point-icon"><i class="<?php echo esc_attr( $icon ); ?>"></i></div>
										<div>
											<h4><?php echo esc_html( $title ); ?></h4>
											<p><?php echo esc_html( $desc ); ?></p>
										</div>
									</div>
								<?php endwhile;
							else : 
								$default_points = array(
									array( 'icon' => 'fa-solid fa-certificate', 'title' => 'Fully Licensed & Certified', 'desc' => 'All technicians hold state certifications and undergo continuous training.' ),
									array( 'icon' => 'fa-solid fa-clock', 'title' => 'On-Time, Every Time', 'desc' => "We respect your schedule. If we're late, your service is free." ),
									array( 'icon' => 'fa-solid fa-tag', 'title' => 'Upfront, Flat-Rate Pricing', 'desc' => "No hidden fees, no surprises. You'll know the price before we start." ),
									array( 'icon' => 'fa-solid fa-medal', 'title' => '100% Satisfaction Guarantee', 'desc' => "Not happy? We'll make it right — free of charge, every time." ),
								);
								foreach ( $default_points as $point ) : ?>
									<div class="why-point">
										<div class="why-point-icon"><i class="<?php echo esc_attr( $point['icon'] ); ?>"></i></div>
										<div>
											<h4><?php echo esc_html( $point['title'] ); ?></h4>
											<p><?php echo esc_html( $point['desc'] ); ?></p>
										</div>
									</div>
								<?php endforeach;
							endif;
							?>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- ========== PROCESS ========== -->
		<section class="process section" id="process">
			<div class="container">
				<div class="section-header reveal">
					<span class="label"><?php echo esc_html( get_field( 'process_label' ) ?: 'How It Works' ); ?></span>
					<h2><?php echo esc_html( get_field( 'process_title' ) ?: 'Simple. Fast. Done Right.' ); ?></h2>
					<p><?php echo esc_html( get_field( 'process_description' ) ?: 'Getting your home back to perfect takes just 4 easy steps.' ); ?></p>
				</div>
				<div class="process-steps">
					<?php 
					$step_index = 0;
					if ( have_rows( 'process_steps' ) ) :
						while ( have_rows( 'process_steps' ) ) : the_row();
							$step_num = get_sub_field( 'step_number' ) ?: sprintf( '%02d', $step_index + 1 );
							$icon = get_sub_field( 'icon_class' ) ?: 'fa-solid fa-phone';
							$title = get_sub_field( 'title' ) ?: 'Step';
							$desc = get_sub_field( 'description' ) ?: 'Description';
							?>
							<?php if ( $step_index > 0 ) : ?>
								<div class="process-connector"></div>
							<?php endif; ?>
							<div class="process-step reveal" data-delay="<?php echo esc_attr( $step_index * 100 ); ?>">
								<div class="step-number"><?php echo esc_html( $step_num ); ?></div>
								<div class="step-icon"><i class="<?php echo esc_attr( $icon ); ?>"></i></div>
								<h3><?php echo esc_html( $title ); ?></h3>
								<p><?php echo esc_html( $desc ); ?></p>
							</div>
							<?php 
							$step_index++;
						endwhile;
					else : 
						$default_steps = array(
							array( 'num' => '01', 'icon' => 'fa-solid fa-phone', 'title' => 'Call or Book Online', 'desc' => 'Reach us 24/7 by phone or schedule through our easy online form in under 2 minutes.' ),
							array( 'num' => '02', 'icon' => 'fa-solid fa-magnifying-glass', 'title' => 'We Diagnose the Issue', 'desc' => 'Our expert technicians arrive on time, assess the situation, and explain everything clearly.' ),
							array( 'num' => '03', 'icon' => 'fa-solid fa-screwdriver-wrench', 'title' => 'Quality Work, Fast', 'desc' => 'We get the job done right using top-grade parts and time-tested techniques.' ),
							array( 'num' => '04', 'icon' => 'fa-solid fa-circle-check', 'title' => 'Final Inspection', 'desc' => 'We test everything, clean up the workspace, and walk you through what was done.' ),
						);
						foreach ( $default_steps as $i => $step ) : ?>
							<?php if ( $i > 0 ) : ?>
								<div class="process-connector"></div>
							<?php endif; ?>
							<div class="process-step reveal" data-delay="<?php echo esc_attr( $i * 100 ); ?>">
								<div class="step-number"><?php echo esc_html( $step['num'] ); ?></div>
								<div class="step-icon"><i class="<?php echo esc_attr( $step['icon'] ); ?>"></i></div>
								<h3><?php echo esc_html( $step['title'] ); ?></h3>
								<p><?php echo esc_html( $step['desc'] ); ?></p>
							</div>
						<?php endforeach;
					endif;
					?>
				</div>
			</div>
		</section>

		<!-- ========== TESTIMONIALS ========== -->
		<section class="testimonials section" id="testimonials">
			<div class="container">
				<div class="section-header reveal">
					<span class="label"><?php echo esc_html( get_field( 'testimonials_label' ) ?: 'Customer Reviews' ); ?></span>
					<h2><?php echo esc_html( get_field( 'testimonials_title' ) ?: 'What Our Clients Say' ); ?></h2>
				</div>
				<div class="testimonial-slider">
					<div class="testimonial-track" id="testimonialTrack">
						<?php 
						if ( have_rows( 'testimonials' ) ) :
							while ( have_rows( 'testimonials' ) ) : the_row();
								$quote = get_sub_field( 'quote' ) ?: 'Quote';
								$name = get_sub_field( 'reviewer_name' ) ?: 'Name';
								$title = get_sub_field( 'reviewer_title' ) ?: 'Title';
								$photo = get_sub_field( 'reviewer_photo' );
								?>
								<div class="testimonial-card">
									<div class="stars">★★★★★</div>
									<p>"<?php echo esc_html( $quote ); ?>"</p>
									<div class="reviewer">
										<?php if ( $photo ) : ?>
											<img src="<?php echo esc_url( $photo ); ?>" alt="<?php echo esc_attr( $name ); ?>"/>
										<?php else : ?>
											<img src="https://randomuser.me/api/portraits/lego/1.jpg" alt="<?php echo esc_attr( $name ); ?>"/>
										<?php endif; ?>
										<div>
											<strong><?php echo esc_html( $name ); ?></strong>
											<span><?php echo esc_html( $title ); ?></span>
										</div>
									</div>
								</div>
							<?php endwhile;
						else :
							$default_testimonials = array(
								array( 'quote' => 'FlowForce fixed our burst pipe at 2am within an hour of calling. Incredible service — professional, clean, and fair priced. These guys are lifesavers!', 'name' => 'Sarah M.', 'title' => 'Homeowner, Austin TX', 'photo' => 'https://randomuser.me/api/portraits/women/44.jpg' ),
								array( 'quote' => 'Our HVAC system was failing in July heat. FlowForce came same-day, gave us a flat-rate quote, and had us cool again by evening. Absolutely recommend!', 'name' => 'James R.', 'title' => 'Property Manager', 'photo' => 'https://randomuser.me/api/portraits/men/32.jpg' ),
								array( 'quote' => "I've used FlowForce three times now. Every technician is polite, knowledgeable, and leaves everything spotless. Genuinely the best in the business.", 'name' => 'Linda K.', 'title' => 'Long-time Customer', 'photo' => 'https://randomuser.me/api/portraits/women/68.jpg' ),
								array( 'quote' => 'Upfront pricing, no surprises on the bill, and the technician explained every step. Replaced my water heater in under 3 hours. 10/10 experience.', 'name' => 'Derek T.', 'title' => 'Small Business Owner', 'photo' => 'https://randomuser.me/api/portraits/men/75.jpg' ),
							);
							foreach ( $default_testimonials as $testimonial ) : ?>
								<div class="testimonial-card">
									<div class="stars">★★★★★</div>
									<p>"<?php echo esc_html( $testimonial['quote'] ); ?>"</p>
									<div class="reviewer">
										<img src="<?php echo esc_url( $testimonial['photo'] ); ?>" alt="<?php echo esc_attr( $testimonial['name'] ); ?>"/>
										<div>
											<strong><?php echo esc_html( $testimonial['name'] ); ?></strong>
											<span><?php echo esc_html( $testimonial['title'] ); ?></span>
										</div>
									</div>
								</div>
							<?php endforeach;
						endif;
						?>
					</div>
					<div class="slider-controls">
						<button class="slider-btn" id="prevBtn"><i class="fa-solid fa-chevron-left"></i></button>
						<div class="slider-dots" id="sliderDots"></div>
						<button class="slider-btn" id="nextBtn"><i class="fa-solid fa-chevron-right"></i></button>
					</div>
				</div>
			</div>
		</section>

		<!-- ========== CONTACT ========== -->
		<section class="contact section" id="contact">
			<div class="container">
				<div class="contact-inner">
					<div class="contact-info reveal">
						<span class="label"><?php echo esc_html( get_field( 'contact_label' ) ?: 'Get In Touch' ); ?></span>
						<h2><?php echo esc_html( get_field( 'contact_title' ) ?: 'Request a Free Estimate' ); ?></h2>
						<p><?php echo esc_html( get_field( 'contact_description' ) ?: "Fill out the form and we'll get back to you within 30 minutes during business hours." ); ?></p>

						<div class="contact-details">
							<?php $phone = get_field( 'phone_number', 'option' ); ?>
							<a href="tel:<?php echo esc_attr( $phone ?: '+18005551234' ); ?>" class="contact-detail">
								<i class="fa-solid fa-phone"></i>
								<div><strong><?php esc_html_e( 'Phone', 'asdfafa' ); ?></strong><span><?php echo esc_html( $phone ?: '+1 (800) 555-1234' ); ?></span></div>
							</a>
							<?php $email = get_field( 'email_address', 'option' ); ?>
							<a href="mailto:<?php echo esc_attr( $email ?: 'hello@flowforce.com' ); ?>" class="contact-detail">
								<i class="fa-solid fa-envelope"></i>
								<div><strong><?php esc_html_e( 'Email', 'asdfafa' ); ?></strong><span><?php echo esc_html( $email ?: 'hello@flowforce.com' ); ?></span></div>
							</a>
							<div class="contact-detail">
								<i class="fa-solid fa-location-dot"></i>
								<div><strong><?php esc_html_e( 'Service Area', 'asdfafa' ); ?></strong><span><?php echo esc_html( get_field( 'service_area' ) ?: 'Greater Metro & Suburbs' ); ?></span></div>
							</div>
							<div class="contact-detail">
								<i class="fa-solid fa-clock"></i>
								<div><strong><?php esc_html_e( 'Hours', 'asdfafa' ); ?></strong><span><?php echo esc_html( get_field( 'business_hours' ) ?: 'Mon–Sat: 7am–8pm | 24/7 Emergency' ); ?></span></div>
							</div>
						</div>
					</div>

					<div class="contact-form-wrap reveal">
						<?php 
						// Use Contact Form 7 shortcode if available, otherwise show HTML form
						if ( shortcode_exists( 'contact-form-7' ) ) :
							echo do_shortcode( '[contact-form-7 id="contact-form" title="Contact Form"]' );
						else :
						?>
						<form class="contact-form" id="contactForm">
							<div class="form-row">
								<div class="form-group">
									<label><?php esc_html_e( 'Full Name', 'asdfafa' ); ?></label>
									<input type="text" placeholder="<?php esc_attr_e( 'John Smith', 'asdfafa' ); ?>" required />
								</div>
								<div class="form-group">
									<label><?php esc_html_e( 'Phone Number', 'asdfafa' ); ?></label>
									<input type="tel" placeholder="+1 (555) 000-0000" required />
								</div>
							</div>
							<div class="form-group">
								<label><?php esc_html_e( 'Email Address', 'asdfafa' ); ?></label>
								<input type="email" placeholder="<?php esc_attr_e( 'john@email.com', 'asdfafa' ); ?>" required />
							</div>
							<div class="form-group">
								<label><?php esc_html_e( 'Service Needed', 'asdfafa' ); ?></label>
								<select required>
									<option value=""><?php esc_html_e( 'Select a service...', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'Plumbing Repair', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'AC Repair / Installation', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'Heating / Furnace', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'Water Heater', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'Indoor Air Quality', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'Emergency Service', 'asdfafa' ); ?></option>
									<option><?php esc_html_e( 'Other', 'asdfafa' ); ?></option>
								</select>
							</div>
							<div class="form-group">
								<label><?php esc_html_e( 'Message', 'asdfafa' ); ?></label>
								<textarea rows="4" placeholder="<?php esc_attr_e( 'Describe the issue...', 'asdfafa' ); ?>"></textarea>
							</div>
							<button type="submit" class="btn btn-primary btn-full">
								<i class="fa-solid fa-paper-plane"></i> <?php esc_html_e( 'Send Request', 'asdfafa' ); ?>
							</button>
							<div class="form-success" id="formSuccess">
								<i class="fa-solid fa-circle-check"></i> <?php esc_html_e( "Thanks! We'll contact you within 30 minutes.", 'asdfafa' ); ?>
							</div>
						</form>
						<?php endif; ?>
					</div>
				</div>
			</div>
		</section>

	</main><!-- #main -->

<?php
get_footer();