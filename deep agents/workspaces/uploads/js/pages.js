/* =============================================
   RAPIDFLOW PLUMBING — PAGE-SPECIFIC JS
   Home, Services, About, Reviews, Contact
   ============================================= */

(function () {
  'use strict';

  const page = document.body.dataset.page;

  /* ========================================
     HOME PAGE
  ======================================== */
  if (page === 'home') {

    /* Hero form submission */
    const heroForm = document.getElementById('heroForm');
    if (heroForm) {
      heroForm.addEventListener('submit', (e) => {
        e.preventDefault();
        showSuccessMessage(heroForm, 'Thanks! We\'ll call you within 15 minutes.');
      });
    }

    /* Auto-rotate service card highlight */
    const serviceCards = document.querySelectorAll('.service-card');
    if (serviceCards.length) {
      let current = 0;
      setInterval(() => {
        serviceCards.forEach(c => c.style.borderBottomColor = 'transparent');
        serviceCards[current].style.borderBottomColor = 'var(--orange)';
        current = (current + 1) % serviceCards.length;
      }, 2500);
    }
  }

  /* ========================================
     SERVICES PAGE
  ======================================== */
  if (page === 'services') {

    /* Category filter buttons */
    const filterBtns = document.querySelectorAll('.filter-btn');
    const serviceCards = document.querySelectorAll('.service-detail-card');

    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const cat = btn.dataset.cat;
        serviceCards.forEach(card => {
          if (cat === 'all' || card.dataset.category === cat) {
            card.style.display = 'flex';
            card.style.animation = 'fadeInUp 0.4s ease both';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  }

  /* ========================================
     REVIEWS PAGE
  ======================================== */
  if (page === 'reviews') {

    /* Sort reviews */
    const sortSelect = document.getElementById('sortReviews');
    const reviewsList = document.getElementById('reviewsList');
    if (sortSelect && reviewsList) {
      sortSelect.addEventListener('change', () => {
        const cards = Array.from(reviewsList.querySelectorAll('.review-full-card'));
        const val = sortSelect.value;
        cards.sort((a, b) => {
          if (val === 'newest') return parseInt(b.dataset.ts) - parseInt(a.dataset.ts);
          if (val === 'highest') return parseInt(b.dataset.rating) - parseInt(a.dataset.rating);
          if (val === 'lowest') return parseInt(a.dataset.rating) - parseInt(b.dataset.rating);
          return 0;
        });
        cards.forEach(c => reviewsList.appendChild(c));
      });
    }

    /* Load more */
    const loadMoreBtn = document.getElementById('loadMoreReviews');
    const hiddenReviews = document.querySelectorAll('.review-full-card.hidden');
    let shown = 0;
    if (loadMoreBtn && hiddenReviews.length) {
      loadMoreBtn.addEventListener('click', () => {
        const batch = Array.from(hiddenReviews).slice(shown, shown + 3);
        batch.forEach(c => {
          c.classList.remove('hidden');
          c.style.animation = 'fadeInUp 0.4s ease both';
        });
        shown += batch.length;
        if (shown >= hiddenReviews.length) loadMoreBtn.style.display = 'none';
      });
    }
  }

  /* ========================================
     CONTACT PAGE
  ======================================== */
  if (page === 'contact') {

    /* Contact form submission */
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
      contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const btn = contactForm.querySelector('button[type="submit"]');
        btn.textContent = 'Sending...';
        btn.disabled = true;
        setTimeout(() => {
          showSuccessMessage(contactForm, '✅ Message received! We\'ll be in touch within 1 hour during business hours.');
          btn.textContent = 'Send Message';
          btn.disabled = false;
          contactForm.reset();
        }, 1200);
      });
    }

    /* Highlight current day in hours table */
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = days[new Date().getDay()];
    document.querySelectorAll('.hours-table tr').forEach(row => {
      const dayCell = row.querySelector('td');
      if (dayCell && dayCell.textContent.trim() === today) {
        row.classList.add('today');
      }
    });
  }

  /* ========================================
     ABOUT PAGE
  ======================================== */
  if (page === 'about') {
    /* Animate team cards on scroll - handled by common reveal */
  }

  /* ========================================
     SHARED UTILITIES
  ======================================== */

  function showSuccessMessage(form, message) {
    let msg = form.querySelector('.success-msg');
    if (!msg) {
      msg = document.createElement('div');
      msg.className = 'success-msg';
      msg.style.cssText = `
        background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7;
        border-radius: 8px; padding: 14px 18px; margin-top: 14px;
        font-size: 15px; font-weight: 600; text-align: center;
        animation: fadeInUp 0.4s ease both;
      `;
      form.appendChild(msg);
    }
    msg.textContent = message;
    setTimeout(() => { if (msg.parentNode) msg.remove(); }, 6000);
  }

  /* Inject shared CSS animation */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(16px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  document.head.appendChild(style);

})();
