/* ═════════════════════════════════════════════════════
   Peak-End Experience Script
   峰值體驗：進度感 / 揭露儀式 / 終點光環
   ═════════════════════════════════════════════════════ */

// ────────── 1. Scroll Reveal（漸顯） ──────────
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('in');
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -80px 0px' });

document.querySelectorAll(
  '.section-title, .section-sub, .section-label, .concept__text, .concept__image, ' +
  '.layer, .apple, .ref, .craft__photo, .craft__layer, .event, .quote__card, ' +
  '.past__grid figure, .cta h2, .cta p, .cta__meta, .cta__mark'
).forEach(el => {
  el.classList.add('reveal');
  io.observe(el);
});

// ────────── 2. Hero Parallax ──────────
const heroBg = document.querySelector('.hero__bg');
if (heroBg) {
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y < window.innerHeight) {
      heroBg.style.transform = `scale(1.05) translateY(${y * 0.25}px)`;
    }
  }, { passive: true });
}

// ────────── 3. 頂部 Scroll Progress 金線（Connection） ──────────
const progressBar = document.createElement('div');
progressBar.className = 'scroll-progress';
progressBar.innerHTML = '<div class="scroll-progress__bar"></div>';
document.body.prepend(progressBar);
const progressInner = progressBar.querySelector('.scroll-progress__bar');
window.addEventListener('scroll', () => {
  const h = document.documentElement;
  const scrolled = h.scrollTop / (h.scrollHeight - h.clientHeight);
  progressInner.style.transform = `scaleX(${Math.max(0, Math.min(1, scrolled))})`;
}, { passive: true });

// ────────── 4. 金額 Count-up 揭露儀式（Peak） ──────────
// 對所有標記 .count-up 的元素執行動畫：data-target 是最終值
function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }

function runCountUp(el) {
  const target = parseInt(el.dataset.target, 10);
  if (!Number.isFinite(target)) return;
  const duration = 1600;
  const start = performance.now();
  const format = (n) => n.toLocaleString('en-US');
  function step(now) {
    const t = Math.min(1, (now - start) / duration);
    const v = Math.floor(target * easeOutExpo(t));
    el.textContent = format(v);
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = format(target);
  }
  requestAnimationFrame(step);
}

const countObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      runCountUp(e.target);
      countObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.4 });

document.querySelectorAll('.count-up').forEach(el => {
  el.textContent = '0';
  countObserver.observe(el);
});

// ────────── 5. 聖杯 Hover · 離子場加速（Elevation） ──────────
document.querySelectorAll('.apple').forEach(card => {
  const sigil = card.querySelector('.sigil');
  if (!sigil) return;
  card.addEventListener('mouseenter', () => sigil.classList.add('sigil--charged'));
  card.addEventListener('mouseleave', () => sigil.classList.remove('sigil--charged'));
});

// ────────── 6. Hero 標題 · 字元錯落浮現（Peak Entry） ──────────
document.querySelectorAll('.hero__title-main').forEach((el) => {
  const text = el.textContent;
  el.textContent = '';
  [...text].forEach((ch, i) => {
    const span = document.createElement('span');
    span.className = 'hero__char';
    span.textContent = ch;
    span.style.animationDelay = `${0.7 + i * 0.07}s`;
    el.appendChild(span);
  });
});
