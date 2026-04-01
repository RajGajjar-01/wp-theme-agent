/* =============================================
   FLOWFORCE — PLUMBING & HVAC | script.js
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {

  /* ---- Loader ---- */
  const loader = document.getElementById('loader');
  window.addEventListener('load', () => {
    setTimeout(() => {
      loader.classList.add('hidden');
      document.body.style.overflow = '';
      // Trigger initial reveal after load
      revealOnScroll();
    }, 800);
  });
  document.body.style.overflow = 'hidden';


  /* ---- Navbar scroll behavior ---- */
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  }, { passive: true });


  /* ---- Hamburger Menu ---- */
  const hamburger = document.getElementById('hamburger');
  const navLinks  = document.getElementById('navLinks');
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    navLinks.classList.toggle('open');
  });
  // Close on link click
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      navLinks.classList.remove('open');
    });
  });


  /* ---- Smooth scroll for all anchor links ---- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = navbar.offsetHeight + 16;
        const top    = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });


  /* ---- Reveal on scroll ---- */
  function revealOnScroll() {
    const reveals = document.querySelectorAll('.reveal');
    reveals.forEach(el => {
      const rect = el.getBoundingClientRect();
      const inView = rect.top < window.innerHeight - 60;
      if (inView) {
        const delay = el.dataset.delay || 0;
        setTimeout(() => el.classList.add('visible'), parseInt(delay));
      }
    });
  }
  window.addEventListener('scroll', revealOnScroll, { passive: true });
  revealOnScroll(); // run on load


  /* ---- Testimonial Slider ---- */
  const track  = document.getElementById('testimonialTrack');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const dotsWrap = document.getElementById('sliderDots');

  const cards = track ? track.querySelectorAll('.testimonial-card') : [];
  let current = 0;
  let autoSlideTimer;

  if (cards.length && track) {
    // Create dots
    cards.forEach((_, i) => {
      const dot = document.createElement('div');
      dot.className = 'dot' + (i === 0 ? ' active' : '');
      dot.addEventListener('click', () => goTo(i));
      dotsWrap.appendChild(dot);
    });

    function goTo(index) {
      current = (index + cards.length) % cards.length;
      track.style.transform = `translateX(-${current * 100}%)`;
      dotsWrap.querySelectorAll('.dot').forEach((d, i) => {
        d.classList.toggle('active', i === current);
      });
    }

    function startAutoSlide() {
      autoSlideTimer = setInterval(() => goTo(current + 1), 5000);
    }
    function stopAutoSlide() { clearInterval(autoSlideTimer); }

    prevBtn.addEventListener('click', () => { stopAutoSlide(); goTo(current - 1); startAutoSlide(); });
    nextBtn.addEventListener('click', () => { stopAutoSlide(); goTo(current + 1); startAutoSlide(); });

    // Touch support
    let touchStartX = 0;
    track.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
    track.addEventListener('touchend',   e => {
      const diff = touchStartX - e.changedTouches[0].clientX;
      if (Math.abs(diff) > 50) {
        stopAutoSlide();
        goTo(diff > 0 ? current + 1 : current - 1);
        startAutoSlide();
      }
    });

    startAutoSlide();
  }


  /* ---- Contact Form ---- */
  const form        = document.getElementById('contactForm');
  const formSuccess = document.getElementById('formSuccess');

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      const btn = form.querySelector('button[type="submit"]');
      btn.textContent = 'Sending…';
      btn.disabled = true;

      // Simulate sending (replace with real API call in production)
      setTimeout(() => {
        form.reset();
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Send Request';
        btn.disabled  = false;
        formSuccess.classList.add('show');
        setTimeout(() => formSuccess.classList.remove('show'), 5000);
      }, 1500);
    });
  }


  /* ---- Back to Top ---- */
  const backToTop = document.getElementById('backToTop');
  window.addEventListener('scroll', () => {
    backToTop.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });


  /* ---- Animate number stats ---- */
  function animateCounter(el, target, suffix = '') {
    const duration = 1800;
    const start    = performance.now();
    const startVal = 0;

    function update(now) {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      const current  = Math.round(startVal + (target - startVal) * eased);
      el.textContent = current + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const statEls = entry.target.querySelectorAll('.stat strong');
        statEls.forEach(el => {
          const text = el.textContent.trim();
          const num  = parseInt(text.replace(/\D/g, ''));
          const suffix = text.replace(/[0-9]/g, '');
          animateCounter(el, num, suffix);
        });
        statsObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  const heroStats = document.querySelector('.hero-stats');
  if (heroStats) statsObserver.observe(heroStats);


  /* ---- Service card stagger on enter ---- */
  const serviceCards = document.querySelectorAll('.service-card.reveal');
  const cardObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay || 0);
        setTimeout(() => entry.target.classList.add('visible'), delay);
        cardObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  serviceCards.forEach(card => cardObserver.observe(card));


  /* ---- Parallax hero image on mousemove ---- */
  const heroSection = document.querySelector('.hero');
  const heroImg     = document.querySelector('.hero-image-wrap img');

  if (heroSection && heroImg && window.innerWidth > 1024) {
    heroSection.addEventListener('mousemove', (e) => {
      const { left, top, width, height } = heroSection.getBoundingClientRect();
      const x = (e.clientX - left) / width  - 0.5;
      const y = (e.clientY - top)  / height - 0.5;
      heroImg.style.transform = `scale(1.05) translate(${x * 12}px, ${y * 8}px)`;
    });
    heroSection.addEventListener('mouseleave', () => {
      heroImg.style.transform = 'scale(1) translate(0, 0)';
    });
  }


  /* ---- Floating cards subtle parallax ---- */
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    const card1   = document.querySelector('.card-1');
    const card2   = document.querySelector('.card-2');
    if (card1) card1.style.transform = `translateY(${scrollY * 0.06}px)`;
    if (card2) card2.style.transform = `translateY(${-scrollY * 0.04}px)`;
  }, { passive: true });


  /* ---- Active nav link highlight on scroll ---- */
  const sections   = document.querySelectorAll('section[id]');
  const navItems   = document.querySelectorAll('.nav-links a');

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navItems.forEach(link => {
          link.style.color = link.getAttribute('href') === `#${id}`
            ? 'var(--text)'
            : '';
        });
      }
    });
  }, { rootMargin: '-50% 0px -50% 0px' });

  sections.forEach(s => sectionObserver.observe(s));

});
