
(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════
  // PARTICLE SYSTEM
  // ═══════════════════════════════════════════════════════════════
  function createParticles() {
    const particleCount = 30;
    const container = document.body;
    
    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.top = Math.random() * 100 + '%';
      particle.style.animationDelay = Math.random() * 20 + 's';
      particle.style.animationDuration = (20 + Math.random() * 10) + 's';
      
      // Random size
      const size = 2 + Math.random() * 4;
      particle.style.width = size + 'px';
      particle.style.height = size + 'px';
      
      // Random opacity
      particle.style.opacity = 0.2 + Math.random() * 0.5;
      
      container.appendChild(particle);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // TOAST NOTIFICATION SYSTEM
  // ═══════════════════════════════════════════════════════════════
  window.showToast = function(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    }[type] || 'ℹ️';
    
    toast.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 24px;">${icon}</div>
        <div style="flex: 1;">
          <div style="font-size: 11px; font-weight: 600; color: var(--fg); margin-bottom: 4px; font-family: var(--mono);">
            ${type.toUpperCase()}
          </div>
          <div style="font-size: 13px; color: var(--fg2); line-height: 1.4;">
            ${message}
          </div>
        </div>
        <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: var(--fg3); cursor: pointer; font-size: 18px; padding: 0; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 4px; transition: all 0.2s;">
          ×
        </button>
      </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove
    setTimeout(() => {
      toast.classList.add('hiding');
      setTimeout(() => toast.remove(), 300);
    }, duration);
    
    return toast;
  };

  // ═══════════════════════════════════════════════════════════════
  // SCROLL REVEAL ANIMATION
  // ═══════════════════════════════════════════════════════════════
  function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.reveal').forEach(el => {
      observer.observe(el);
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // RIPPLE EFFECT ON BUTTONS
  // ═══════════════════════════════════════════════════════════════
  function addRippleEffect() {
    document.addEventListener('click', function(e) {
      const target = e.target.closest('.btn-auth, .sgo, .btn-loc, .ibtn, .q-card, .nav-tab, .map-tab');
      if (!target) return;
      
      const ripple = document.createElement('span');
      ripple.style.position = 'absolute';
      ripple.style.borderRadius = '50%';
      ripple.style.background = 'rgba(255,255,255,0.5)';
      ripple.style.width = '20px';
      ripple.style.height = '20px';
      ripple.style.pointerEvents = 'none';
      ripple.style.animation = 'ripple 0.6s ease-out';
      
      const rect = target.getBoundingClientRect();
      ripple.style.left = (e.clientX - rect.left - 10) + 'px';
      ripple.style.top = (e.clientY - rect.top - 10) + 'px';
      
      target.style.position = 'relative';
      target.style.overflow = 'hidden';
      target.appendChild(ripple);
      
      setTimeout(() => ripple.remove(), 600);
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // SMOOTH SCROLL TO TOP
  // ═══════════════════════════════════════════════════════════════
  function addScrollToTop() {
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '↑';
    scrollBtn.style.cssText = `
      position: fixed;
      bottom: 30px;
      right: 30px;
      width: 50px;
      height: 50px;
      border-radius: 50%;
      background: linear-gradient(135deg, #0d9488, #0284c7);
      border: none;
      color: white;
      font-size: 24px;
      cursor: pointer;
      opacity: 0;
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 9999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    scrollBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    document.body.appendChild(scrollBtn);
    
    // Show/hide based on scroll
    const scrollContainers = document.querySelectorAll('.msgs, .news-scroll, .alertsScroll, .guide-body, .maps-body');
    scrollContainers.forEach(container => {
      container.addEventListener('scroll', () => {
        if (container.scrollTop > 300) {
          scrollBtn.style.opacity = '1';
          scrollBtn.style.pointerEvents = 'all';
        } else {
          scrollBtn.style.opacity = '0';
          scrollBtn.style.pointerEvents = 'none';
        }
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // ENHANCED HOVER SOUND (Optional - can be disabled)
  // ═══════════════════════════════════════════════════════════════
  function addHoverSounds() {
    // Subtle hover feedback (visual only, no actual sound)
    const hoverElements = document.querySelectorAll('.q-card, .nav-tab, .map-tab, .lang-btn');
    hoverElements.forEach(el => {
      el.addEventListener('mouseenter', function() {
        this.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // LOADING INDICATOR
  // ═══════════════════════════════════════════════════════════════
  window.showLoading = function(message = 'Loading...') {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.style.cssText = `
      position: fixed;
      inset: 0;
      background: rgba(2,12,27,0.95);
      backdrop-filter: blur(10px);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 99999;
      animation: fadeIn 0.3s ease-out;
    `;
    
    loader.innerHTML = `
      <div class="loading-spinner" style="width: 60px; height: 60px; border-width: 4px; margin-bottom: 20px;"></div>
      <div style="color: var(--teal2); font-family: var(--mono); font-size: 14px; letter-spacing: 2px;">
        ${message}
      </div>
    `;
    
    document.body.appendChild(loader);
    return loader;
  };

  window.hideLoading = function() {
    const loader = document.getElementById('global-loader');
    if (loader) {
      loader.style.animation = 'fadeOut 0.3s ease-out forwards';
      setTimeout(() => loader.remove(), 300);
    }
  };

  // ═══════════════════════════════════════════════════════════════
  // ENHANCED CARD TILT EFFECT (3D)
  // ═══════════════════════════════════════════════════════════════
  function addCardTilt() {
    const cards = document.querySelectorAll('.glass-card, .w-card, .sq-risk-box, .g-item');
    
    cards.forEach(card => {
      card.addEventListener('mousemove', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
      });
      
      card.addEventListener('mouseleave', function() {
        this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // TYPING INDICATOR FOR CHAT
  // ═══════════════════════════════════════════════════════════════
  window.showTypingIndicator = function() {
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'msg ai';
    indicator.style.cssText = 'padding: 12px 16px;';
    
    indicator.innerHTML = `
      <div style="display: flex; gap: 4px; align-items: center;">
        <div class="typing-dot" style="width: 8px; height: 8px; background: var(--teal2); border-radius: 50%; animation: tdot 1.4s infinite;"></div>
        <div class="typing-dot" style="width: 8px; height: 8px; background: var(--teal2); border-radius: 50%; animation: tdot 1.4s infinite 0.2s;"></div>
        <div class="typing-dot" style="width: 8px; height: 8px; background: var(--teal2); border-radius: 50%; animation: tdot 1.4s infinite 0.4s;"></div>
      </div>
    `;
    
    const msgBox = document.getElementById('msgBox');
    if (msgBox) {
      msgBox.appendChild(indicator);
      msgBox.scrollTop = msgBox.scrollHeight;
    }
    
    return indicator;
  };

  window.hideTypingIndicator = function() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
  };

  // ═══════════════════════════════════════════════════════════════
  // INITIALIZE ALL ENHANCEMENTS
  // ═══════════════════════════════════════════════════════════════
  function init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }

    console.log('🛡 RAKSHA UI Enhancements Loading...');
    
    // Create particles
    createParticles();
    
    // Initialize scroll reveal
    setTimeout(initScrollReveal, 100);
    
    // Add ripple effects
    addRippleEffect();
    
    // Add scroll to top button
    addScrollToTop();
    
    // Add hover sounds
    addHoverSounds();
    
    // Add card tilt effect
    setTimeout(addCardTilt, 500);
    
    // Show welcome toast
    setTimeout(() => {
      if (document.getElementById('app').classList.contains('on')) {
        showToast('Welcome to RAKSHA Disaster Intelligence Platform', 'success', 3000);
      }
    }, 1000);
    
    console.log('✅ RAKSHA UI Enhancements Loaded');
  }

  // Start initialization
  init();

  // ═══════════════════════════════════════════════════════════════
  // EXPORT FUNCTIONS TO WINDOW
  // ═══════════════════════════════════════════════════════════════
  window.RAKSHA_UI = {
    showToast,
    showLoading,
    hideLoading,
    showTypingIndicator,
    hideTypingIndicator
  };

})();
