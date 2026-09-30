/* 手機版頭 .mobile-quick-links 可橫向捲動時，右緣淡出漸層提示還能往右滑；捲到最右端自動消失。
   首頁與 SSR 作品頁共用；樣式在 site.css（.topbar.quick-fade::after，僅 ≤980px 生效）。 */
(function () {
  'use strict';
  var bar = document.querySelector('.topbar');
  var links = bar && bar.querySelector('.mobile-quick-links');
  if (!links) return;
  function update() {
    bar.style.setProperty('--quick-h', links.offsetHeight + 'px');
    bar.classList.toggle('quick-end', links.scrollLeft + links.clientWidth >= links.scrollWidth - 2);
  }
  bar.classList.add('quick-fade');
  links.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();
