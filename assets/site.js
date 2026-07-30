(function () {
  'use strict';

  // ── Config ──
  var HOVER_DELAY = 1200;
  var LEAVE_DELAY = 300;
  var POPUP_DELAY = 600;
  var SLIDE_INTERVAL = 3000;

  // Category labels
  var CAT_LABELS = {
    business: '主題活動',
    party: '春酒尾牙',
    magic: '魔法學院',
    civil: '戶政改造'
  };

  // 章節式相簿：每個分類 = 一個章節（英文分類名／中文章名／敘事一句／完整作品頁）
  var CHAPTER_META = {
    business: { en: 'BUSINESS', name: '主題活動', lead: '把品牌的故事，變成一個走得進去的現場。', more: '/services/business-event/' },
    party:    { en: 'PARTY',    name: '春酒尾牙', lead: '一年一度的犒賞，值得一個被記住的舞台。', more: '/services/party-spring-banquet/' },
    magic:    { en: 'MAGIC',    name: '魔法學院', lead: '讓活動長出一個世界觀，大人小孩都想留下來。', more: '/services/magic-academy/' },
    civil:    { en: 'CIVIL',    name: '戶政改造', lead: '把辦證的冷空間，變成想拍照打卡的場景。', more: '/services/civil-makeover/' }
  };

  // ── State ──
  var ytReady = false;
  var ytLoading = false;
  var player = null;
  var hoverTimer = null;
  var leaveTimer = null;
  var currentVideoId = null;
  var isMuted = true;
  var pendingVideoId = null;
  var articlesData = [];
  var articleMap = {};

  // Popup state
  var popupTimer = null;
  var popupHideImgTimer = null;
  var popupCard = null;
  var slideTimer = null;
  var slideIndex = 0;
  var slideImages = [];

  // ── DOM refs ──
  var heroBg, heroVideoLayer, heroMuteBtn, allCards;
  var popup, popupImg, popupImgNext, popupDots, popupTag, popupDesc, popupPlayBtn, popupLinkBtn, popupExpandBtn, popupMedia;
  var popupFullDesc, popupGallery;
  var detailModal, detailTag, detailTitle, detailDescription, detailLink, detailVideoToggle;
  var detailStageImage, detailStageVideo, detailThumbs, detailMediaStatus, detailMediaNote;
  var detailGalleryPrev, detailGalleryNext;
  var lightbox, lightboxImg, lightboxVideo, lightboxCounter;
  var lightboxImages = [];
  var lightboxIndex = 0;
  var currentPopupArticle = null;
  var currentDetailArticle = null;
  var currentDetailMode = 'image';
  var currentDetailImageIndex = 0;
  var detailOpenedFromPage = false;
  var toast;

  // ══════════════════════════════════════════
  //  DATA FETCHING + RENDERING
  // ══════════════════════════════════════════

  function fetchArticles() {
    // Try API first, fall back to inline data
    return fetch('/api/articles')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        articlesData = data.articles || [];
        buildArticleMap();
        return articlesData;
      })
      .catch(function () {
        // Fallback: try direct JSON file
        return fetch('/data/articles.json')
          .then(function (r) { return r.json(); })
          .then(function (data) {
            articlesData = data.articles || [];
            buildArticleMap();
            return articlesData;
          });
      });
  }

  function buildArticleMap() {
    articleMap = {};
    articlesData.forEach(function (a) {
      articleMap[a.id] = a;
    });
  }

  function getArticleUrl(article) {
    if (!article) return window.location.href;
    // 對外網址一律走語意化 slug（沒有 slug 才 fallback 回 id）。
    // 注意：站內 hash routing 的 #detail/{id} 仍然用 id，不受這裡影響。
    if (article.slug || article.id) return '/works/' + (article.slug || article.id);
    if (!article.linkUrl || article.linkUrl === '#') return window.location.href;
    if (/^https?:\/\//i.test(article.linkUrl)) return article.linkUrl;
    return window.location.origin + article.linkUrl;
  }

  function getAbsoluteArticleUrl(article) {
    var url = getArticleUrl(article);
    if (/^https?:\/\//i.test(url)) return url;
    return window.location.origin + url;
  }

  // ── Render Top 10 ──
  function renderTop10(articles) {
    var rail = document.querySelector('.top10-rail');
    if (!rail) return;
    rail.innerHTML = '';

    articles.forEach(function (a, i) {
      var card = document.createElement('article');
      card.className = 'top10-card';

      var rank = document.createElement('span');
      rank.className = 'top10-rank';
      rank.textContent = i + 1;

      var link = document.createElement('a');
      link.className = 'poster-card';
      link.href = getArticleUrl(a);
      link.setAttribute('data-article-id', a.id);
      link.setAttribute('data-hero-img', a.heroImage);
      if (a.videoId) {
        link.setAttribute('data-video', a.videoId);
        if (a.videoVertical) link.setAttribute('data-video-vertical', '');
      }

      var img = document.createElement('img');
      img.src = a.heroImage;
      img.alt = a.title;
      img.loading = 'lazy';

      var span = document.createElement('span');
      span.textContent = a.title;

      link.appendChild(img);
      link.appendChild(span);
      card.appendChild(rank);
      card.appendChild(link);
      rail.appendChild(card);
    });
  }

  function buildAwardBadge(award) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'award-badge award-badge-' + (award.level || '').toLowerCase();
    btn.textContent = (award.label || ((award.year || '') + ' ' + award.name + ' ' + award.level)).trim();
    btn.title = '查看獎項介紹頁';
    btn.setAttribute('aria-label', btn.textContent + '，點擊查看獎項介紹');
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      window.location.href = award.detailUrl || '/muse-2026.html';
    });
    return btn;
  }

  // ── Render Category Chapter（章節式相簿：沉浸開場 + 章內拼貼陳列）──
  function renderChapter(category, articles, chapterNo) {
    var section = document.getElementById(category);
    if (!section) return;
    section.innerHTML = '';
    if (!articles.length) return;

    var meta = CHAPTER_META[category] ||
      { en: (category || '').toUpperCase(), name: CAT_LABELS[category] || category, lead: '', more: '#' };

    // 依 sortOrder 排序；代表大圖優先取 featured（featuredOrder 最小），否則 sortOrder 最前
    var sorted = articles.slice().sort(function (a, b) { return (a.sortOrder || 0) - (b.sortOrder || 0); });
    var featured = sorted.filter(function (a) { return a.featured; })
      .sort(function (a, b) { return (a.featuredOrder || 0) - (b.featuredOrder || 0); });
    var hero = featured.length ? featured[0] : sorted[0];
    // 章內陳列 = 其餘作品（排除代表作），保留完整清單不截斷
    var rest = sorted.filter(function (a) { return a.id !== hero.id; });

    // ── 沉浸開場：滿寬大圖 + 左下漸層敘事 ──
    var open = document.createElement('a');
    open.className = 'chapter-open';
    open.href = getArticleUrl(hero);
    open.setAttribute('data-article-id', hero.id);
    // 沿用現有 #detail/{id} 機制開 detail modal（比照其他卡片設定 detailOpenedFromPage）
    open.addEventListener('click', function (e) {
      e.preventDefault();
      hidePopup();
      detailOpenedFromPage = true;
      window.location.hash = 'detail/' + hero.id;
    });

    var openImg = document.createElement('img');
    openImg.src = hero.heroImage;
    openImg.alt = hero.title || meta.name;
    openImg.loading = 'lazy';
    open.appendChild(openImg);

    var num = chapterNo < 10 ? '0' + chapterNo : '' + chapterNo;
    var cap = document.createElement('div');
    cap.className = 'chapter-open-cap';
    cap.innerHTML =
      '<div class="chapter-eyebrow"><span class="chapter-dot"></span>CHAPTER ' + num + ' · ' + meta.en + '</div>' +
      '<h2 class="chapter-title"></h2>' +
      '<p class="chapter-lead"></p>';
    cap.querySelector('.chapter-title').textContent = meta.name;
    cap.querySelector('.chapter-lead').textContent = meta.lead;
    open.appendChild(cap);
    section.appendChild(open);

    // ── 章內拼貼陳列（masonry columns，大小交錯）──
    if (rest.length) {
      var lineup = document.createElement('div');
      lineup.className = 'chapter-lineup';
      rest.forEach(function (a) {
        var link = document.createElement('a');
        link.className = 'chapter-card';
        link.href = getArticleUrl(a);
        link.setAttribute('data-article-id', a.id);
        link.setAttribute('data-hero-img', a.heroImage);
        if (a.videoId) {
          link.setAttribute('data-video', a.videoId);
          if (a.videoVertical) link.setAttribute('data-video-vertical', '');
        }

        var img = document.createElement('img');
        img.src = a.heroImage;
        img.alt = a.title;
        img.loading = 'lazy';

        var span = document.createElement('span');
        span.textContent = a.title;

        link.appendChild(img);
        if (a.awards && a.awards.length) link.appendChild(buildAwardBadge(a.awards[0]));
        link.appendChild(span);
        lineup.appendChild(link);
      });
      section.appendChild(lineup);
    }

    // ── 章末 CTA：看完整 N 件 XX 作品 ──
    var more = document.createElement('a');
    more.className = 'chapter-more';
    more.href = meta.more;
    more.innerHTML = '<span class="chapter-dot"></span>';
    more.appendChild(document.createTextNode('看完整 ' + articles.length + ' 件' + meta.name + '作品 →'));
    section.appendChild(more);
  }

  function renderAll() {
    var featured = articlesData.filter(function (a) { return a.featured; })
      .sort(function (a, b) { return (a.featuredOrder || 0) - (b.featuredOrder || 0); });

    var business = articlesData.filter(function (a) { return a.category === 'business'; });
    var party = articlesData.filter(function (a) { return a.category === 'party' || /尾牙/.test(a.title || ''); });
    var magic = articlesData.filter(function (a) { return a.category === 'magic'; });
    var civil = articlesData.filter(function (a) { return a.category === 'civil'; });

    renderTop10(featured);
    // 章節顯示順序沿用首頁現有分類順序（business→party→magic→civil = CHAPTER 01→04）
    renderChapter('business', business, 1);
    renderChapter('party', party, 2);
    renderChapter('magic', magic, 3);
    renderChapter('civil', civil, 4);
  }

  // ══════════════════════════════════════════
  //  YOUTUBE API
  // ══════════════════════════════════════════

  function ensureYTApi() {
    if (ytReady || ytLoading) return;
    ytLoading = true;
    var tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);
  }

  window.onYouTubeIframeAPIReady = function () {
    ytReady = true;
    ytLoading = false;
    createPlayer();
  };

  function createPlayer() {
    player = new YT.Player('hero-yt-player', {
      width: '100%',
      height: '100%',
      playerVars: {
        autoplay: 0, controls: 0, modestbranding: 1, rel: 0,
        showinfo: 0, mute: 1, loop: 1, playsinline: 1,
        enablejsapi: 1, origin: window.location.origin
      },
      events: {
        onReady: onPlayerReady,
        onStateChange: onPlayerStateChange,
        onError: onPlayerError
      }
    });
  }

  function onPlayerReady() {
    if (pendingVideoId) {
      playVideo(pendingVideoId);
      pendingVideoId = null;
    }
  }

  function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
      heroVideoLayer.classList.add('is-active');
    }
    if (event.data === YT.PlayerState.ENDED) {
      player.seekTo(0);
      player.playVideo();
    }
  }

  function onPlayerError() { stopVideoPreview(); }

  // ══════════════════════════════════════════
  //  HERO TRANSITIONS
  // ══════════════════════════════════════════

  function swapHeroImage(src) {
    if (!src || heroBg.getAttribute('src') === src) return;
    heroBg.classList.add('is-swapping');
    setTimeout(function () {
      heroBg.setAttribute('src', src);
      heroBg.onload = function () { heroBg.classList.remove('is-swapping'); };
      setTimeout(function () { heroBg.classList.remove('is-swapping'); }, 400);
    }, 250);
  }

  function playVideo(videoId) {
    if (!player || !ytReady) { pendingVideoId = videoId; return; }
    if (currentVideoId === videoId) return;
    currentVideoId = videoId;
    player.loadVideoById({ videoId: videoId, startSeconds: 0 });
    if (isMuted) player.mute(); else player.unMute();
    if (heroMuteBtn) heroMuteBtn.hidden = false;
  }

  function stopVideoPreview() {
    heroVideoLayer.classList.remove('is-active');
    heroVideoLayer.classList.remove('is-vertical');
    var wasPlaying = currentVideoId;
    currentVideoId = null;
    pendingVideoId = null;
    if (heroMuteBtn) heroMuteBtn.hidden = true;
    if (wasPlaying) {
      setTimeout(function () {
        if (!currentVideoId && player && ytReady) {
          try { player.stopVideo(); } catch (e) {}
        }
      }, 650);
    }
  }

  // ══════════════════════════════════════════
  //  CARD HOVER → HERO
  // ══════════════════════════════════════════

  function onCardEnter(card) {
    clearTimeout(leaveTimer);
    clearTimeout(hoverTimer);

    var heroImg = card.getAttribute('data-hero-img');
    var videoId = card.getAttribute('data-video');

    swapHeroImage(heroImg);

    allCards.forEach(function (c) { c.classList.remove('is-previewing'); });
    card.classList.add('is-previewing');

    if (videoId) {
      var isVertical = card.hasAttribute('data-video-vertical');
      heroVideoLayer.classList.toggle('is-vertical', isVertical);
      ensureYTApi();
      hoverTimer = setTimeout(function () { playVideo(videoId); }, HOVER_DELAY);
    } else {
      stopVideoPreview();
    }

    // Popup
    showPopupForCard(card);
  }

  function onCardLeave(card) {
    clearTimeout(hoverTimer);
    leaveTimer = setTimeout(function () {
      stopVideoPreview();
      allCards.forEach(function (c) { c.classList.remove('is-previewing'); });
    }, LEAVE_DELAY);

    // Popup: delay hide, cancel if mouse enters popup
    scheduleHidePopup();
  }

  // ══════════════════════════════════════════
  //  POPUP
  // ══════════════════════════════════════════

  function getArticleForCard(card) {
    var id = card.getAttribute('data-article-id');
    return id ? articleMap[id] : null;
  }

  function showPopupForCard(card) {
    clearTimeout(popupTimer);
    if (window.innerWidth <= 980) return;

    popupTimer = setTimeout(function () {
      var article = getArticleForCard(card);
      if (!article) return;

      popupCard = card;
      fillPopup(article);
      positionPopup(card);

      popup.hidden = false;
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          popup.classList.add('is-visible');
        });
      });

      // Start slideshow if no video
      if (!article.videoId && article.images && article.images.length > 1) {
        startSlideshow(article.images);
      }
    }, POPUP_DELAY);
  }

  function clearPopupVideo() {
    if (popupHideImgTimer) {
      clearTimeout(popupHideImgTimer);
      popupHideImgTimer = null;
    }
    var old = popupMedia.querySelector('.popup-yt-iframe');
    if (old) old.remove();
  }

  function fillPopup(article) {
    // Stop previous slideshow & video
    stopSlideshow();
    clearPopupVideo();

    // Image
    popupImg.src = article.heroImage;
    popupImg.classList.remove('is-hidden');
    popupImgNext.classList.add('is-hidden');

    // Video: embed autoplay iframe inside popup
    if (article.videoId) {
      var iframe = document.createElement('iframe');
      iframe.className = 'popup-yt-iframe';
      iframe.allow = 'autoplay; encrypted-media';
      iframe.setAttribute('allowfullscreen', '');
      iframe.src = 'https://www.youtube.com/embed/' + article.videoId +
        '?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&loop=1' +
        '&playlist=' + article.videoId + '&playsinline=1';
      popupMedia.appendChild(iframe);
      // Hide image once video loads
      iframe.style.opacity = '0';
      iframe.style.transition = 'opacity .35s ease';
      iframe.onload = function () {
        popupHideImgTimer = setTimeout(function () {
          iframe.style.opacity = '1';
        }, 900);
      };
      // 保底：onload 若未觸發（慢網/封鎖），2.5 秒後仍淡入，避免影片永久隱形
      setTimeout(function () { iframe.style.opacity = '1'; }, 2500);
      popupDots.style.display = 'none';
    }

    // Tag
    popupTag.textContent = CAT_LABELS[article.category] || article.category;

    // Description (short, 2-line clamp)
    popupDesc.textContent = article.description || '';

    // Store current article for buttons
    currentPopupArticle = article;

    // Reset expand state
    popup.classList.remove('is-expanded');

    // Fill expand section
    popupFullDesc.textContent = article.description || '';
    popupGallery.innerHTML = '';
    if (article.images && article.images.length > 0) {
      article.images.forEach(function (src, i) {
        var img = document.createElement('img');
        img.src = src;
        img.alt = article.title + ' ' + (i + 1);
        img.loading = 'lazy';
        img.onclick = function () { openLightbox(article.images, i); };
        popupGallery.appendChild(img);
      });
    }

    // ▶ Play button: open larger detail modal with video/gallery/description
    popupPlayBtn.onclick = function (e) {
      e.preventDefault();
      e.stopPropagation();
      detailOpenedFromPage = true;
      window.location.hash = 'detail/' + article.id;
    };

    // 🔗 Copy link — links to 作品詳情 modal via hash
    popupLinkBtn.onclick = function (e) {
      e.preventDefault();
      e.stopPropagation();
      var url = getAbsoluteArticleUrl(article);
      navigator.clipboard.writeText(url).then(function () {
        showToast('已複製連結');
      });
    };

    // Dots (slideshow indicator for no-video cards)
    if (article.images && article.images.length > 1 && !article.videoId) {
      popupDots.innerHTML = '';
      article.images.forEach(function (_, i) {
        var dot = document.createElement('span');
        if (i === 0) dot.className = 'is-active';
        popupDots.appendChild(dot);
      });
      popupDots.style.display = '';
    } else {
      popupDots.style.display = 'none';
    }
  }

  function positionPopup(card) {
    var rect = card.getBoundingClientRect();
    var pw = 350;

    // Center horizontally on card
    var left = rect.left + (rect.width - pw) / 2;
    // Center vertically on card (popup image area aligns with card)
    var top = rect.top + (rect.height / 2) - (pw * 9 / 32); // align media center with card center

    // Boundary corrections
    left = Math.max(8, Math.min(left, window.innerWidth - pw - 8));
    top = Math.max(8, top);
    // Don't overflow bottom
    if (top + 400 > window.innerHeight) {
      top = window.innerHeight - 420;
    }

    popup.style.transformOrigin = 'center center';
    popup.style.left = left + 'px';
    popup.style.top = top + 'px';
  }

  function hidePopup() {
    clearTimeout(popupTimer);
    stopSlideshow();
    clearPopupVideo();
    popup.classList.remove('is-visible');
    popupCard = null;
    setTimeout(function () {
      if (!popup.classList.contains('is-visible')) {
        popup.hidden = true;
      }
    }, 220);
  }

  function scheduleHidePopup() {
    clearTimeout(popupTimer);
    popupTimer = setTimeout(function () {
      hidePopup();
    }, 300);
  }

  // ── Slideshow ──
  function startSlideshow(images) {
    slideImages = images;
    slideIndex = 0;
    slideTimer = setInterval(function () {
      slideIndex = (slideIndex + 1) % slideImages.length;
      crossfadeImage(slideImages[slideIndex], slideIndex);
    }, SLIDE_INTERVAL);
  }

  function crossfadeImage(src, idx) {
    popupImgNext.src = src;
    popupImgNext.classList.remove('is-hidden');
    popupImg.classList.add('is-hidden');

    // After transition, swap roles
    setTimeout(function () {
      popupImg.src = src;
      popupImg.classList.remove('is-hidden');
      popupImgNext.classList.add('is-hidden');
    }, 650);

    // Update dots
    var dots = popupDots.querySelectorAll('span');
    dots.forEach(function (d, i) {
      d.classList.toggle('is-active', i === idx);
    });
  }

  function stopSlideshow() {
    clearInterval(slideTimer);
    slideTimer = null;
  }

  // ── Detail Modal ──

  function setDetailMedia(mode, imageIndex) {
    var images;

    if (!currentDetailArticle) return;
    if (typeof imageIndex === 'number') currentDetailImageIndex = imageIndex;

    images = currentDetailArticle.images && currentDetailArticle.images.length
      ? currentDetailArticle.images
      : [currentDetailArticle.heroImage];

    currentDetailMode = mode;

    if (mode === 'video' && currentDetailArticle.videoId) {
      detailStageImage.hidden = true;
      detailStageVideo.hidden = false;
      detailStageVideo.src = 'https://www.youtube.com/embed/' + currentDetailArticle.videoId +
        '?autoplay=1&mute=1&rel=0&modestbranding=1&playsinline=1';
      detailMediaStatus.textContent = '正在播放影片';
    } else {
      currentDetailImageIndex = Math.max(0, Math.min(currentDetailImageIndex, images.length - 1));
      detailStageVideo.hidden = true;
      detailStageVideo.src = '';
      detailStageImage.hidden = false;
      detailStageImage.src = images[currentDetailImageIndex];
      detailStageImage.alt = currentDetailArticle.title + ' ' + (currentDetailImageIndex + 1);
      detailMediaStatus.textContent = '精彩花絮 ' + (currentDetailImageIndex + 1) + ' / ' + images.length;
    }

    Array.from(detailThumbs.querySelectorAll('.detail-thumb')).forEach(function (btn, idx) {
      btn.classList.toggle('is-active', currentDetailMode === 'image' && idx === currentDetailImageIndex);
    });

    if (detailVideoToggle) {
      detailVideoToggle.hidden = !currentDetailArticle.videoId || currentDetailMode === 'video';
      detailVideoToggle.disabled = currentDetailMode === 'video';
      detailVideoToggle.textContent = currentDetailMode === 'video' ? '正在播放影片' : '▶ 播放影片';
    }

    updateDetailGalleryArrows();
  }

  function updateDetailGalleryArrows() {
    if (!detailGalleryPrev || !detailGalleryNext || !currentDetailArticle) return;
    var images = currentDetailArticle.images || [];
    detailGalleryPrev.disabled = currentDetailImageIndex <= 0;
    detailGalleryNext.disabled = currentDetailImageIndex >= images.length - 1;
  }

  function scrollThumbIntoView(index) {
    if (!detailThumbs) return;
    var thumb = detailThumbs.children[index];
    if (thumb) thumb.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }

  function renderDetailThumbs(article) {
    detailThumbs.innerHTML = '';

    if (!article.images || !article.images.length) return;

    article.images.forEach(function (src, i) {
      var btn = document.createElement('button');
      var img = document.createElement('img');

      btn.className = 'detail-thumb';
      btn.type = 'button';
      btn.onclick = function () { setDetailMedia('image', i); };

      img.src = src;
      img.alt = article.title + ' ' + (i + 1);
      img.loading = 'lazy';

      btn.appendChild(img);
      detailThumbs.appendChild(btn);
    });

    detailThumbs.scrollLeft = 0;
  }

  function openDetailModal(article) {
    if (!article || !detailModal) return;

    currentDetailArticle = article;
    currentDetailImageIndex = 0;

    detailTag.textContent = CAT_LABELS[article.category] || article.category;
    detailTitle.textContent = article.title || '';
    detailDescription.textContent = article.description || '';
    if (detailLink) detailLink.style.display = 'none';
    detailMediaNote.textContent = (article.images ? article.images.length : 0) + ' 張相片' +
      (article.videoId ? ' / 含影片介紹' : '');
    renderDetailThumbs(article);
    if (detailVideoToggle) {
      detailVideoToggle.hidden = !article.videoId;
      detailVideoToggle.disabled = false;
      detailVideoToggle.textContent = '▶ 播放影片';
    }
    setDetailMedia(article.videoId ? 'video' : 'image', 0);

    detailModal.hidden = false;
    // Must update arrows AFTER modal is visible (hidden elements have 0 dimensions)
    requestAnimationFrame(updateDetailGalleryArrows);
    document.body.style.overflow = 'hidden';
    hidePopup();
    stopVideoPreview();
  }

  function closeDetailModal() {
    if (!detailModal) return;
    detailModal.hidden = true;
    detailStageVideo.src = '';
    document.body.style.overflow = '';
    currentDetailArticle = null;
    currentDetailMode = 'image';
  }

  function requestCloseDetailModal() {
    if (detailOpenedFromPage && /^#detail\//.test(window.location.hash)) {
      history.back();
    } else {
      history.replaceState(null, '', window.location.pathname + window.location.search);
      closeDetailModal();
    }
  }

  // ══════════════════════════════════════════
  //  LIGHTBOX
  // ══════════════════════════════════════════

  function openLightbox(images, startIndex) {
    lightboxImages = images;
    lightboxIndex = startIndex || 0;
    lightboxVideo.hidden = true;
    lightboxVideo.src = '';
    lightboxImg.hidden = false;
    lightboxImg.src = lightboxImages[lightboxIndex];
    updateLightboxCounter();
    lightbox.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function openLightboxVideo(videoId) {
    lightboxImages = [];
    lightboxImg.hidden = true;
    lightboxVideo.hidden = false;
    lightboxVideo.src = 'https://www.youtube.com/embed/' + videoId +
      '?autoplay=1&mute=0&rel=0&modestbranding=1';
    lightboxCounter.textContent = '';
    lightbox.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightbox.hidden = true;
    lightboxVideo.src = '';
    document.body.style.overflow = '';
  }

  function lightboxPrev() {
    if (lightboxImages.length === 0) return;
    lightboxIndex = (lightboxIndex - 1 + lightboxImages.length) % lightboxImages.length;
    lightboxImg.src = lightboxImages[lightboxIndex];
    updateLightboxCounter();
  }

  function lightboxNext() {
    if (lightboxImages.length === 0) return;
    lightboxIndex = (lightboxIndex + 1) % lightboxImages.length;
    lightboxImg.src = lightboxImages[lightboxIndex];
    updateLightboxCounter();
  }

  function updateLightboxCounter() {
    lightboxCounter.textContent = (lightboxIndex + 1) + ' / ' + lightboxImages.length;
  }

  // ══════════════════════════════════════════
  //  EXPAND TOGGLE
  // ══════════════════════════════════════════

  function toggleExpand() {
    popup.classList.toggle('is-expanded');
  }

  // ── Toast ──
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('is-visible');
    setTimeout(function () {
      toast.classList.remove('is-visible');
    }, 2000);
  }

  // ══════════════════════════════════════════
  //  MOBILE TOUCH
  // ══════════════════════════════════════════

  function bindTouch() {
    var lastTapped = null;
    allCards.forEach(function (card) {
      card.addEventListener('click', function (e) {
        if (window.innerWidth > 980) return;
        e.preventDefault();
        if (lastTapped === card) {
          // Second tap: open detail modal
          lastTapped = null;
          var articleId = card.getAttribute('data-article-id');
          var article = articleMap[articleId];
          if (article) {
            detailOpenedFromPage = true;
            window.location.hash = 'detail/' + article.id;
          }
          return;
        }
        lastTapped = card;
        swapHeroImage(card.getAttribute('data-hero-img'));
        allCards.forEach(function (c) { c.classList.remove('is-previewing'); });
        card.classList.add('is-previewing');
        setTimeout(function () { lastTapped = null; }, 3000);
      });
    });
  }

  // ══════════════════════════════════════════
  //  MUTE TOGGLE
  // ══════════════════════════════════════════

  function bindMute() {
    if (!heroMuteBtn) return;
    heroMuteBtn.addEventListener('click', function () {
      if (!player) return;
      isMuted = !isMuted;
      if (isMuted) player.mute(); else player.unMute();
      heroMuteBtn.classList.toggle('is-muted', isMuted);
    });
  }

  // ══════════════════════════════════════════
  //  DRAG-TO-SCROLL
  // ══════════════════════════════════════════

  function bindDragScroll() {
    var rails = Array.from(document.querySelectorAll('.top10-rail'));
    rails.forEach(function (rail) {
      var isDown = false, startX, scrollLeft, hasDragged;

      rail.addEventListener('mousedown', function (e) {
        isDown = true;
        hasDragged = false;
        rail.style.cursor = 'grabbing';
        startX = e.pageX - rail.offsetLeft;
        scrollLeft = rail.scrollLeft;
      });

      rail.addEventListener('mouseleave', function () {
        isDown = false;
        rail.style.cursor = '';
      });

      rail.addEventListener('mouseup', function () {
        isDown = false;
        rail.style.cursor = '';
      });

      rail.addEventListener('mousemove', function (e) {
        if (!isDown) return;
        e.preventDefault();
        var x = e.pageX - rail.offsetLeft;
        var walk = (x - startX) * 1.5;
        if (Math.abs(walk) > 5) hasDragged = true;
        rail.scrollLeft = scrollLeft - walk;
      });

      // Prevent click on cards after drag
      rail.addEventListener('click', function (e) {
        if (hasDragged) {
          e.preventDefault();
          e.stopPropagation();
          hasDragged = false;
        }
      }, true);
    });
  }

  function updateShelfArrowState(rail, prevBtn, nextBtn) {
    if (!rail || !prevBtn || !nextBtn) return;
    prevBtn.disabled = rail.scrollLeft <= 4;
    nextBtn.disabled = rail.scrollLeft + rail.clientWidth >= rail.scrollWidth - 4;
  }

  function bindShelfArrows() {
    var rails = Array.from(document.querySelectorAll('.top10-rail'));

    rails.forEach(function (rail) {
      var head = rail.parentElement.querySelector('.section-head');
      var controls = head && head.querySelector('.shelf-arrows');
      var prevBtn, nextBtn, step;

      if (!head) return;

      if (!controls) {
        controls = document.createElement('div');
        controls.className = 'shelf-arrows';

        prevBtn = document.createElement('button');
        prevBtn.className = 'shelf-arrow shelf-arrow-prev';
        prevBtn.type = 'button';
        prevBtn.setAttribute('aria-label', '向左查看更多');
        prevBtn.innerHTML = '&#8249;';

        nextBtn = document.createElement('button');
        nextBtn.className = 'shelf-arrow shelf-arrow-next';
        nextBtn.type = 'button';
        nextBtn.setAttribute('aria-label', '向右查看更多');
        nextBtn.innerHTML = '&#8250;';

        controls.appendChild(prevBtn);
        controls.appendChild(nextBtn);
        head.appendChild(controls);

        prevBtn.addEventListener('click', function () {
          step = Math.max(rail.clientWidth * 0.85, 280);
          rail.scrollBy({ left: -step, behavior: 'smooth' });
        });

        nextBtn.addEventListener('click', function () {
          step = Math.max(rail.clientWidth * 0.85, 280);
          rail.scrollBy({ left: step, behavior: 'smooth' });
        });

        rail.addEventListener('scroll', function () {
          updateShelfArrowState(rail, prevBtn, nextBtn);
        });

        window.addEventListener('resize', function () {
          updateShelfArrowState(rail, prevBtn, nextBtn);
        });
      } else {
        prevBtn = controls.querySelector('.shelf-arrow-prev');
        nextBtn = controls.querySelector('.shelf-arrow-next');
      }

      updateShelfArrowState(rail, prevBtn, nextBtn);
    });
  }

  // ══════════════════════════════════════════
  //  CASE COUNT
  // ══════════════════════════════════════════

  function updateCaseCount() {
    var el = document.getElementById('case-count');
    if (!el) return;
    el.textContent = articlesData.length + ' 件作品';
  }

  // ══════════════════════════════════════════
  //  EVENT BINDING (works on dynamic cards)
  // ══════════════════════════════════════════

  function rebindCardEvents() {
    allCards = Array.from(document.querySelectorAll('.poster-card, .landscape-card, .chapter-card'));

    allCards.forEach(function (card) {
      card.addEventListener('mouseenter', function () { onCardEnter(card); });
      card.addEventListener('mouseleave', function () { onCardLeave(card); });
      card.addEventListener('click', function (e) {
        e.preventDefault();
        var articleId = card.getAttribute('data-article-id');
        var article = articleMap[articleId];
        if (article) {
          hidePopup();
          detailOpenedFromPage = true;
          window.location.hash = 'detail/' + article.id;
        }
      });
    });

    bindTouch();
    bindDragScroll();
    bindShelfArrows();
    updateCaseCount();
  }

  // ══════════════════════════════════════════
  //  INIT
  // ══════════════════════════════════════════

  document.addEventListener('DOMContentLoaded', function () {
    // Phase 1.5: mark JS-hydrated so the SSR featured block can hide via CSS.
    document.body.classList.add('js-ready');
    heroBg = document.querySelector('.hero-bg');
    heroVideoLayer = document.getElementById('hero-video-layer');
    heroMuteBtn = document.getElementById('hero-mute-toggle');
    popup = document.getElementById('card-popup');
    popupMedia = popup.querySelector('.card-popup-media');
    popupImg = popup.querySelector('.card-popup-img');
    popupImgNext = popup.querySelector('.card-popup-img-next');
    popupDots = popup.querySelector('.card-popup-dots');
    popupTag = popup.querySelector('.popup-tag');
    popupDesc = popup.querySelector('.card-popup-desc');
    popupPlayBtn = popup.querySelector('.popup-btn-play');
    popupLinkBtn = popup.querySelector('.popup-btn-link');
    popupExpandBtn = popup.querySelector('.popup-btn-expand');
    popupFullDesc = popup.querySelector('.card-popup-full-desc');
    popupGallery = popup.querySelector('.card-popup-gallery');
    toast = document.getElementById('toast');

    detailModal = document.getElementById('detail-modal');
    detailTag = document.getElementById('detail-tag');
    detailTitle = document.getElementById('detail-title');
    detailDescription = document.getElementById('detail-description');
    detailLink = document.getElementById('detail-link');
    detailVideoToggle = document.getElementById('detail-video-toggle');
    detailStageImage = document.getElementById('detail-stage-image');
    detailStageVideo = document.getElementById('detail-stage-video');
    detailThumbs = document.getElementById('detail-thumbs');
    detailMediaStatus = document.getElementById('detail-media-status');
    detailMediaNote = document.getElementById('detail-media-note');
    detailGalleryPrev = document.getElementById('detail-gallery-prev');
    detailGalleryNext = document.getElementById('detail-gallery-next');

    // Lightbox
    lightbox = document.getElementById('lightbox');
    lightboxImg = document.getElementById('lightbox-img');
    lightboxVideo = document.getElementById('lightbox-video');
    lightboxCounter = document.getElementById('lightbox-counter');

    lightbox.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
    lightbox.querySelector('.lightbox-prev').addEventListener('click', lightboxPrev);
    lightbox.querySelector('.lightbox-next').addEventListener('click', lightboxNext);
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });
    detailModal.querySelector('.detail-modal-close').addEventListener('click', requestCloseDetailModal);
    detailModal.querySelector('.detail-modal-backdrop').addEventListener('click', requestCloseDetailModal);
    detailVideoToggle.addEventListener('click', function () {
      if (currentDetailArticle && currentDetailArticle.videoId) setDetailMedia('video');
    });
    detailGalleryPrev.addEventListener('click', function () {
      if (currentDetailImageIndex > 0) {
        setDetailMedia('image', currentDetailImageIndex - 1);
        scrollThumbIntoView(currentDetailImageIndex);
      }
    });
    detailGalleryNext.addEventListener('click', function () {
      var images = currentDetailArticle && currentDetailArticle.images;
      if (images && currentDetailImageIndex < images.length - 1) {
        setDetailMedia('image', currentDetailImageIndex + 1);
        scrollThumbIntoView(currentDetailImageIndex);
      }
    });
    window.addEventListener('resize', updateDetailGalleryArrows);

    // Mouse drag scroll for 精彩花絮
    (function () {
      var isDown = false, wasDragged = false, startX, scrollStart;
      detailThumbs.addEventListener('mousedown', function (e) {
        if (e.button !== 0) return;
        isDown = true;
        wasDragged = false;
        startX = e.clientX;
        scrollStart = detailThumbs.scrollLeft;
        detailThumbs.style.cursor = 'grabbing';
        e.preventDefault(); // prevent native button/image drag
      });
      document.addEventListener('mousemove', function (e) {
        if (!isDown) return;
        var dx = e.clientX - startX;
        if (Math.abs(dx) > 4) wasDragged = true;
        detailThumbs.scrollLeft = scrollStart - dx;
      });
      document.addEventListener('mouseup', function () {
        if (!isDown) return;
        isDown = false;
        detailThumbs.style.cursor = '';
      });
      // Block click on thumbnails if user just dragged
      detailThumbs.addEventListener('click', function (e) {
        if (wasDragged) {
          e.stopPropagation();
          e.preventDefault();
          wasDragged = false;
        }
      }, true);
    })();

    // Keyboard: Esc close, arrows navigate
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (!lightbox.hidden) { closeLightbox(); return; }
        if (!detailModal.hidden) { requestCloseDetailModal(); return; }
      }
      // Detail modal arrow navigation (image mode)
      if (!detailModal.hidden && currentDetailMode === 'image') {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          e.preventDefault();
          var imgs = currentDetailArticle && currentDetailArticle.images;
          if (e.key === 'ArrowLeft' && imgs && currentDetailImageIndex > 0) {
            setDetailMedia('image', currentDetailImageIndex - 1);
            scrollThumbIntoView(currentDetailImageIndex);
          }
          if (e.key === 'ArrowRight' && imgs && currentDetailImageIndex < imgs.length - 1) {
            setDetailMedia('image', currentDetailImageIndex + 1);
            scrollThumbIntoView(currentDetailImageIndex);
          }
          return;
        }
      }
      // Lightbox arrow navigation
      if (lightbox.hidden) return;
      if (e.key === 'ArrowLeft') lightboxPrev();
      if (e.key === 'ArrowRight') lightboxNext();
    });

    // Expand button
    popupExpandBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      toggleExpand();
    });

    // Popup mouse events: keep popup open when mouse enters it
    popup.addEventListener('mouseenter', function () {
      clearTimeout(popupTimer);
      clearTimeout(leaveTimer);
    });
    popup.addEventListener('mouseleave', function () {
      scheduleHidePopup();
      leaveTimer = setTimeout(function () {
        stopVideoPreview();
        allCards.forEach(function (c) { c.classList.remove('is-previewing'); });
      }, LEAVE_DELAY);
    });

    bindMute();

    // Fetch data and render
    fetchArticles().then(function () {
      renderAll();
      rebindCardEvents();
      // Deep link: open 作品詳情 if hash matches #detail/<id>
      checkDetailHash();
    });

    window.addEventListener('hashchange', checkDetailHash);
  });

  function checkDetailHash() {
    var m = window.location.hash.match(/^#detail\/(.+)$/);
    if (m && articleMap[m[1]]) {
      openDetailModal(articleMap[m[1]]);
    } else if (detailModal && !detailModal.hidden) {
      closeDetailModal();
    }
  }
})();
