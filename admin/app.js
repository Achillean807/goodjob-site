'use strict';

var articles = [];
var accountsCache = [];
var authHeader = '';
var currentAccount = null;
var editImages = [];
var currentCatFilter = '';
var rowDragSrcId = null;
var rowDropTarget = null;
var rowDropClass = '';
var confirmAction = null;
var gallerySortable = null;
var lbIndex = 0;
var selectedAccountUsername = '';

var CAT_LABELS = {
  business: '主題活動',
  party: '春酒尾牙',
  magic: '魔法學院',
  civil: '戶政改造'
};

var CAT_CLASSES = {
  business: 'badge-business',
  party: 'badge-party',
  magic: 'badge-magic',
  civil: 'badge-civil'
};

var ROLE_LABELS = {
  admin: '管理員',
  editor: '編輯',
  viewer: '檢視者',
  custom: '自訂'
};

var ROLE_PRESETS = {
  admin: ['articles.read', 'articles.write', 'articles.delete', 'uploads.write', 'accounts.manage'],
  editor: ['articles.read', 'articles.write', 'uploads.write'],
  viewer: ['articles.read'],
  custom: []
};

var PERMISSION_LABELS = {
  'articles.read': '讀取作品列表',
  'articles.write': '新增 / 編輯作品',
  'articles.delete': '刪除作品',
  'uploads.write': '上傳圖片',
  'accounts.manage': '帳戶管理'
};

function esc(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function hasPermission(permission) {
  return !!(currentAccount && currentAccount.permissions && currentAccount.permissions.indexOf(permission) !== -1);
}

function thumbUrl(src) {
  if (!src) return src;
  var lower = src.toLowerCase();
  if (lower.indexOf('-thumb.webp') !== -1) return src;
  if (lower.slice(-5) !== '.webp') return src;
  return src.slice(0, -5) + '-thumb.webp';
}

function requirePermission(permission, message) {
  if (hasPermission(permission)) {
    return true;
  }
  toast(message || '你沒有這個操作權限', true);
  return false;
}

function api(method, path, body, options) {
  var opts = {
    method: method,
    headers: {}
  };

  if (authHeader) {
    opts.headers.Authorization = authHeader;
  }

  if (body !== undefined && body !== null) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }

  return fetch(path, opts).then(function(response) {
    var contentType = response.headers.get('Content-Type') || '';
    var parseBody = contentType.indexOf('application/json') !== -1
      ? response.json().catch(function() { return null; })
      : Promise.resolve(null);

    return parseBody.then(function(payload) {
      if (!response.ok) {
        var error = new Error(payload && payload.error ? payload.error : ('API error: ' + response.status));
        error.status = response.status;
        error.payload = payload;

        if (response.status === 401 && !(options && options.suppressLogout)) {
          handleUnauthorized(options && options.silentUnauthorized);
        }
        throw error;
      }
      return payload;
    });
  });
}

function resetLoginError() {
  var errorEl = document.getElementById('login-error');
  errorEl.textContent = '帳號或密碼錯誤';
  errorEl.style.display = 'none';
}

function showLoginError(message) {
  var errorEl = document.getElementById('login-error');
  errorEl.textContent = message || '帳號或密碼錯誤';
  errorEl.style.display = 'block';
}

function handleUnauthorized(silent) {
  sessionStorage.removeItem('auth');
  authHeader = '';
  currentAccount = null;
  accountsCache = [];
  selectedAccountUsername = '';
  document.getElementById('login-pass').value = '';
  document.getElementById('app-screen').style.display = 'none';
  document.getElementById('login-screen').style.display = '';
  closeModal();
  closeAccountsModal();
  closeConfirm();
  closeLightbox();
  applyPermissions();
  if (!silent) {
    showLoginError('登入已失效，請重新登入');
  } else {
    resetLoginError();
  }
}

function fetchSession(options) {
  return api('GET', '/api/session', null, options).then(function(data) {
    currentAccount = data && data.account ? data.account : null;
    applyPermissions();
    return currentAccount;
  });
}

function doLogin() {
  var user = document.getElementById('login-user').value.replace(/^\s+|\s+$/g, '');
  var pass = document.getElementById('login-pass').value;
  if (!user || !pass) {
    showLoginError('請輸入帳號與密碼');
    return;
  }

  resetLoginError();
  authHeader = 'Basic ' + btoa(user + ':' + pass);
  fetchSession({ suppressLogout: true, silentUnauthorized: true })
    .then(function() {
      sessionStorage.setItem('auth', authHeader);
      showApp();
    })
    .catch(function(error) {
      authHeader = '';
      showLoginError(error && error.status === 401 ? '帳號或密碼錯誤' : '登入失敗，請稍後再試');
    });
}

function doLogout() {
  sessionStorage.removeItem('auth');
  authHeader = '';
  currentAccount = null;
  accountsCache = [];
  selectedAccountUsername = '';
  document.getElementById('app-screen').style.display = 'none';
  document.getElementById('login-screen').style.display = '';
  closeModal();
  closeAccountsModal();
  closeConfirm();
  closeLightbox();
  applyPermissions();
  resetLoginError();
}

function showApp() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-screen').style.display = '';
  applyPermissions();
  loadArticles();
}

function restoreSession() {
  var saved = sessionStorage.getItem('auth');
  if (!saved) {
    applyPermissions();
    return;
  }

  authHeader = saved;
  fetchSession({ silentUnauthorized: true })
    .then(function() {
      showApp();
    })
    .catch(function() {
      handleUnauthorized(true);
    });
}

function roleLabel(role) {
  return ROLE_LABELS[role] || role || '未設定';
}

function permissionSummary(permissions) {
  if (!permissions || !permissions.length) {
    return '無';
  }

  var labels = [];
  for (var i = 0; i < permissions.length; i++) {
    labels.push(PERMISSION_LABELS[permissions[i]] || permissions[i]);
  }
  return labels.join('、');
}

function applyPermissions() {
  var sessionUser = document.getElementById('session-user');
  var accountsBtn = document.getElementById('accounts-btn');
  var addBtn = document.getElementById('add-article-btn');
  var modalSaveBtn = document.getElementById('modal-save-btn');
  var galleryUploadBtn = document.getElementById('gallery-upload-btn');
  var heroInput = document.getElementById('hero-input');
  var galleryInput = document.getElementById('gallery-input');
  var lightboxSetHero = document.getElementById('lb-set-hero-btn');
  var lightboxDelete = document.getElementById('lb-delete-btn');

  if (currentAccount) {
    sessionUser.textContent = (currentAccount.name || currentAccount.username) + ' · ' + roleLabel(currentAccount.role);
    sessionUser.style.display = 'inline-flex';
  } else {
    sessionUser.textContent = '';
    sessionUser.style.display = 'none';
  }

  accountsBtn.style.display = hasPermission('accounts.manage') ? '' : 'none';
  addBtn.style.display = hasPermission('articles.write') ? '' : 'none';
  modalSaveBtn.style.display = hasPermission('articles.write') ? '' : 'none';
  galleryUploadBtn.style.display = hasPermission('uploads.write') ? '' : 'none';
  heroInput.disabled = !hasPermission('uploads.write');
  galleryInput.disabled = !hasPermission('uploads.write');
  lightboxSetHero.style.display = hasPermission('articles.write') ? '' : 'none';
  lightboxDelete.style.display = hasPermission('articles.write') ? '' : 'none';

  renderList();
}

function loadArticles() {
  api('GET', '/api/articles').then(function(data) {
    articles = (data && data.articles) || [];
    renderList();
  }).catch(function(error) {
    toast('載入作品失敗：' + error.message, true);
  });
}

function filterCat(btn) {
  currentCatFilter = btn.getAttribute('data-cat') || '';

  var tabs = document.querySelectorAll('.cat-tab');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.remove('is-active');
  }
  btn.classList.add('is-active');
  renderList();
}

function sortVisibleArticles(items) {
  var catOrder = { business: 1, party: 2, magic: 3, civil: 4 };
  return items.sort(function(a, b) {
    var catA = catOrder[a.category] || 99;
    var catB = catOrder[b.category] || 99;
    if (catA !== catB) {
      return catA - catB;
    }
    return (a.sortOrder || 99) - (b.sortOrder || 99);
  });
}

function renderList() {
  var tbody = document.getElementById('article-list');
  if (!tbody) {
    return;
  }

  var q = (document.getElementById('search-input').value || '').toLowerCase();
  var filtered = [];
  var i;

  for (i = 0; i < articles.length; i++) {
    var article = articles[i];
    if (currentCatFilter && article.category !== currentCatFilter) {
      continue;
    }

    var title = String(article.title || '').toLowerCase();
    var desc = String(article.description || '').toLowerCase();
    if (q && title.indexOf(q) === -1 && desc.indexOf(q) === -1) {
      continue;
    }
    filtered.push(article);
  }

  sortVisibleArticles(filtered);

  if (!filtered.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">目前沒有符合條件的作品</td></tr>';
    return;
  }

  var canWrite = hasPermission('articles.write');
  var canDelete = hasPermission('articles.delete');
  var rows = [];

  for (i = 0; i < filtered.length; i++) {
    var item = filtered[i];
    var categoryLabel = CAT_LABELS[item.category] || item.category || '未分類';
    var categoryClass = CAT_CLASSES[item.category] || '';
    var featured = item.featured ? '<span class="badge badge-featured">★ ' + (item.featuredOrder || '') + '</span>' : '—';
    var video = item.videoId ? (item.videoVertical ? '📱' : '🎬') : '—';
    var heroSrc = item.heroImage || (item.images && item.images[0]) || '/assets/images/murayama-favicon.png';
    var imgCount = (item.images || []).length;
    var actionHtml = [];

    if (canWrite) {
      actionHtml.push('<button class="btn btn-secondary btn-sm" onclick="openEdit(\'' + esc(item.id) + '\')">編輯</button>');
    }
    if (canDelete) {
      actionHtml.push('<button class="btn btn-danger btn-sm" onclick="confirmDelete(\'' + esc(item.id) + '\',\'' + esc(item.title) + '\')">刪除</button>');
    }
    if (!actionHtml.length) {
      actionHtml.push('<span class="muted">唯讀</span>');
    }

    rows.push(
      '<tr' + (canWrite ? ' draggable="true"' : '') + ' data-id="' + esc(item.id) + '">' +
        '<td>' + (canWrite ? '<span class="drag-handle">⋮⋮</span>' : '') + '</td>' +
        '<td><img class="thumb" src="' + esc(thumbUrl(heroSrc)) + '" alt="" loading="lazy" decoding="async" onerror="this.onerror=null;this.src=\'' + esc(heroSrc) + '\'"></td>' +
        '<td><strong>' + esc(item.title) + '</strong></td>' +
        '<td><span class="badge ' + categoryClass + '">' + esc(categoryLabel) + '</span></td>' +
        '<td>' + featured + '</td>' +
        '<td>' + imgCount + ' 張</td>' +
        '<td>' + video + '</td>' +
        '<td>' + actionHtml.join(' ') + '</td>' +
      '</tr>'
    );
  }

  tbody.innerHTML = rows.join('');
  bindRowDrag();
}

function bindRowDrag() {
  if (!hasPermission('articles.write')) {
    return;
  }

  var tbody = document.getElementById('article-list');
  var rows = tbody.querySelectorAll('tr[draggable]');
  for (var i = 0; i < rows.length; i++) {
    bindRow(rows[i], tbody);
  }
}

function bindRow(row, tbody) {
  row.addEventListener('dragstart', function(event) {
    rowDragSrcId = row.getAttribute('data-id');
    row.classList.add('is-dragging');
    event.dataTransfer.effectAllowed = 'move';
  });

  row.addEventListener('dragend', function() {
    row.classList.remove('is-dragging');
    clearRowDropState();
  });

  row.addEventListener('dragover', function(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    var rect = row.getBoundingClientRect();
    var mid = rect.top + rect.height / 2;
    var nextClass = event.clientY < mid ? 'drag-above' : 'drag-below';
    if (rowDropTarget === row && rowDropClass === nextClass) {
      return;
    }
    if (rowDropTarget && rowDropTarget !== row) {
      rowDropTarget.classList.remove('drag-above');
      rowDropTarget.classList.remove('drag-below');
    } else if (rowDropTarget === row && rowDropClass) {
      row.classList.remove(rowDropClass);
    }
    row.classList.add(nextClass);
    rowDropTarget = row;
    rowDropClass = nextClass;
  });

  row.addEventListener('dragleave', function(event) {
    var related = event.relatedTarget;
    if (related && row.contains(related)) {
      return;
    }
    if (rowDropTarget === row) {
      row.classList.remove('drag-above');
      row.classList.remove('drag-below');
      rowDropTarget = null;
      rowDropClass = '';
    }
  });

  row.addEventListener('drop', function(event) {
    event.preventDefault();
    clearRowDropState();

    var targetId = row.getAttribute('data-id');
    if (!rowDragSrcId || rowDragSrcId === targetId) {
      return;
    }

    var rect = row.getBoundingClientRect();
    var mid = rect.top + rect.height / 2;
    reorderArticles(rowDragSrcId, targetId, event.clientY < mid);
  });
}

function clearRowDropState() {
  if (rowDropTarget) {
    rowDropTarget.classList.remove('drag-above');
    rowDropTarget.classList.remove('drag-below');
    rowDropTarget = null;
    rowDropClass = '';
  }
}

function reorderArticles(srcId, targetId, insertBefore) {
  if (!requirePermission('articles.write', '你沒有調整排序的權限')) {
    return;
  }

  var filtered = [];
  var i;
  for (i = 0; i < articles.length; i++) {
    if (currentCatFilter && articles[i].category !== currentCatFilter) {
      continue;
    }
    filtered.push(articles[i]);
  }

  sortVisibleArticles(filtered);

  var srcIdx = -1;
  var targetIdx = -1;
  for (i = 0; i < filtered.length; i++) {
    if (filtered[i].id === srcId) {
      srcIdx = i;
    }
    if (filtered[i].id === targetId) {
      targetIdx = i;
    }
  }

  if (srcIdx === -1 || targetIdx === -1) {
    return;
  }

  var moved = filtered.splice(srcIdx, 1)[0];
  var newTargetIdx = -1;
  for (i = 0; i < filtered.length; i++) {
    if (filtered[i].id === targetId) {
      newTargetIdx = i;
      break;
    }
  }

  if (newTargetIdx === -1) {
    newTargetIdx = filtered.length;
  }
  if (!insertBefore) {
    newTargetIdx += 1;
  }
  filtered.splice(newTargetIdx, 0, moved);

  var updates = [];
  var categoryBuckets = {};
  for (i = 0; i < filtered.length; i++) {
    var cat = filtered[i].category || '';
    if (!categoryBuckets[cat]) {
      categoryBuckets[cat] = [];
    }
    categoryBuckets[cat].push(filtered[i]);
  }

  for (var category in categoryBuckets) {
    if (!categoryBuckets.hasOwnProperty(category)) {
      continue;
    }
    for (i = 0; i < categoryBuckets[category].length; i++) {
      var article = categoryBuckets[category][i];
      var newOrder = i + 1;
      if (article.sortOrder !== newOrder) {
        article.sortOrder = newOrder;
        updates.push(article);
      }
    }
  }

  renderList();

  if (!updates.length) {
    return;
  }

  toast('排序更新中...');
  var pending = updates.length;
  var failed = 0;

  for (i = 0; i < updates.length; i++) {
    saveSortOrder(updates[i], function(success) {
      pending -= 1;
      if (!success) {
        failed += 1;
      }
      if (pending === 0) {
        toast(failed ? '部分排序更新失敗' : '排序已儲存', failed > 0);
      }
    });
  }
}

function saveSortOrder(article, done) {
  api('PUT', '/api/articles/' + encodeURIComponent(article.id), {
    sortOrder: article.sortOrder
  }).then(function() {
    done(true);
  }).catch(function() {
    done(false);
  });
}

function openAdd() {
  if (!requirePermission('articles.write', '你沒有新增作品的權限')) {
    return;
  }

  document.getElementById('modal-title').textContent = '新增作品';
  document.getElementById('f-id').value = '';
  document.getElementById('f-title').value = '';
  document.getElementById('f-desc').value = '';
  document.getElementById('f-category').value = 'business';
  document.getElementById('f-sort').value = articles.length + 1;
  document.getElementById('f-featured').checked = false;
  document.getElementById('f-featured-order').value = '1';
  document.getElementById('f-hero').value = '';
  document.getElementById('f-video').value = '';
  document.getElementById('f-vertical').checked = false;
  document.getElementById('hero-input').value = '';
  document.getElementById('gallery-input').value = '';
  editImages = [];
  renderHeroPreview('');
  renderGallery();
  toggleFeaturedOrder();
  document.getElementById('modal').classList.add('is-open');
}

function findArticleById(id) {
  for (var i = 0; i < articles.length; i++) {
    if (articles[i].id === id) {
      return articles[i];
    }
  }
  return null;
}

function openEdit(id) {
  if (!requirePermission('articles.write', '你沒有編輯作品的權限')) {
    return;
  }

  var article = findArticleById(id);
  if (!article) {
    toast('找不到要編輯的作品', true);
    return;
  }

  document.getElementById('modal-title').textContent = '編輯：' + (article.title || '');
  document.getElementById('f-id').value = article.id;
  document.getElementById('f-title').value = article.title || '';
  document.getElementById('f-desc').value = article.description || '';
  document.getElementById('f-category').value = article.category || 'business';
  document.getElementById('f-sort').value = article.sortOrder || 1;
  document.getElementById('f-featured').checked = !!article.featured;
  document.getElementById('f-featured-order').value = article.featuredOrder || 1;
  document.getElementById('f-hero').value = article.heroImage || '';
  document.getElementById('f-video').value = article.videoId || '';
  document.getElementById('f-vertical').checked = !!article.videoVertical;
  document.getElementById('hero-input').value = '';
  document.getElementById('gallery-input').value = '';
  editImages = (article.images || []).slice(0);
  renderHeroPreview(article.heroImage || (article.images && article.images[0]) || '');
  renderGallery();
  toggleFeaturedOrder();
  document.getElementById('modal').classList.add('is-open');
}

function closeModal() {
  document.getElementById('modal').classList.remove('is-open');
}

function toggleFeaturedOrder() {
  var show = document.getElementById('f-featured').checked;
  document.getElementById('featured-order-field').style.display = show ? '' : 'none';
}

function renderHeroPreview(src) {
  var wrap = document.getElementById('hero-preview-wrap');
  var placeholder = document.getElementById('hero-placeholder');
  var img = document.getElementById('hero-preview');

  if (src) {
    img.src = thumbUrl(src);
    wrap.style.display = '';
    placeholder.style.display = 'none';
  } else {
    img.removeAttribute('src');
    wrap.style.display = 'none';
    placeholder.style.display = '';
  }
}

function onHeroFileChange(event) {
  if (!requirePermission('uploads.write', '你沒有上傳圖片的權限')) {
    event.target.value = '';
    return;
  }

  var files = event.target.files;
  if (!files || !files.length) {
    return;
  }

  var articleId = document.getElementById('f-id').value;
  if (!articleId) {
    toast('請先儲存作品再上傳圖片', true);
    event.target.value = '';
    return;
  }

  uploadFiles(articleId, files, function(paths) {
    if (!paths.length) {
      return;
    }

    var heroPath = paths[0];
    document.getElementById('f-hero').value = heroPath;
    renderHeroPreview(heroPath);

    for (var i = 0; i < paths.length; i++) {
      var fullPath = paths[i];
      if (editImages.indexOf(fullPath) === -1) {
        editImages.unshift(fullPath);
      }
    }
    renderGallery();
  });

  event.target.value = '';
}

function removeHero(event) {
  if (!requirePermission('articles.write', '你沒有調整封面圖的權限')) {
    return;
  }

  if (event) {
    event.stopPropagation();
  }
  document.getElementById('f-hero').value = '';
  renderHeroPreview('');
}

function renderGallery() {
  var grid = document.getElementById('gallery-grid');
  var heroVal = document.getElementById('f-hero').value;
  var canWrite = hasPermission('articles.write');
  var parts = [];
  var i;

  for (i = 0; i < editImages.length; i++) {
    var src = editImages[i];
    var isHero = src === heroVal;
    parts.push(
      '<div class="gallery-item' + (isHero ? ' is-hero' : '') + '" data-index="' + i + '" data-src="' + esc(src) + '" onclick="openLightbox(' + i + ')">' +
        '<img src="' + esc(thumbUrl(src)) + '" alt="" loading="lazy" decoding="async" onerror="this.onerror=null;this.src=\'' + esc(src) + '\'">' +
        '<span class="gallery-badge"' + (isHero ? '' : ' style="display:none"') + '>★ 封面</span>' +
        '<span class="gallery-order">' + (i + 1) + '</span>' +
        (canWrite ? '<button class="gallery-remove" onclick="removeGalleryImage(' + i + ',event)">&times;</button>' : '') +
      '</div>'
    );
  }

  grid.innerHTML = parts.join('');

  if (gallerySortable) {
    gallerySortable.destroy();
    gallerySortable = null;
  }

  if (!canWrite) {
    return;
  }

  gallerySortable = new Sortable(grid, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    onEnd: function(evt) {
      var oldIdx = evt.oldIndex;
      var newIdx = evt.newIndex;
      if (oldIdx === newIdx) {
        return;
      }
      var moved = editImages.splice(oldIdx, 1)[0];
      editImages.splice(newIdx, 0, moved);
      syncGalleryIndices();
    }
  });
}

function syncGalleryIndices() {
  var grid = document.getElementById('gallery-grid');
  if (!grid) return;
  var nodes = grid.children;
  for (var i = 0; i < nodes.length; i++) {
    var node = nodes[i];
    node.setAttribute('data-index', i);
    var orderEl = node.querySelector('.gallery-order');
    if (orderEl) orderEl.textContent = (i + 1);
    node.onclick = (function(idx) { return function() { openLightbox(idx); }; })(i);
    var removeBtn = node.querySelector('.gallery-remove');
    if (removeBtn) {
      removeBtn.onclick = (function(idx) {
        return function(ev) { removeGalleryImage(idx, ev); };
      })(i);
    }
  }
}

function setHeroImage(index, event) {
  if (!requirePermission('articles.write', '你沒有調整封面圖的權限')) {
    return;
  }

  if (event) {
    event.stopPropagation();
  }

  var src = editImages[index];
  if (!src) {
    return;
  }
  document.getElementById('f-hero').value = src;
  renderHeroPreview(src);

  var grid = document.getElementById('gallery-grid');
  if (grid) {
    var nodes = grid.children;
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      var isHero = (i === index);
      node.classList.toggle('is-hero', isHero);
      var badge = node.querySelector('.gallery-badge');
      if (badge) badge.style.display = isHero ? '' : 'none';
    }
  }
  toast('已設為封面圖');
}

function openLightbox(index) {
  lbIndex = index;
  updateLightbox();
  document.getElementById('gallery-lightbox').classList.add('is-open');
}

function closeLightbox() {
  document.getElementById('gallery-lightbox').classList.remove('is-open');
}

function navLightbox(direction) {
  if (!editImages.length) {
    return;
  }
  lbIndex = (lbIndex + direction + editImages.length) % editImages.length;
  updateLightbox();
}

function updateLightbox() {
  if (!editImages.length) {
    closeLightbox();
    return;
  }

  var src = editImages[lbIndex];
  var heroVal = document.getElementById('f-hero').value;
  var isHero = src === heroVal;

  document.getElementById('lb-img').src = src;
  document.getElementById('lb-info').textContent = (lbIndex + 1) + ' / ' + editImages.length + (isHero ? '  ★ 目前封面' : '');
}

function lbSetHero() {
  setHeroImage(lbIndex);
  updateLightbox();
}

function lbDelete() {
  if (!requirePermission('articles.write', '你沒有刪除圖庫圖片的權限')) {
    return;
  }

  removeGalleryImage(lbIndex, { stopPropagation: function() {} });
  if (!editImages.length) {
    closeLightbox();
    return;
  }
  if (lbIndex >= editImages.length) {
    lbIndex = editImages.length - 1;
  }
  updateLightbox();
}

function removeGalleryImage(index, event) {
  if (!requirePermission('articles.write', '你沒有刪除圖庫圖片的權限')) {
    return;
  }

  if (event && event.stopPropagation) {
    event.stopPropagation();
  }

  editImages.splice(index, 1);

  var heroVal = document.getElementById('f-hero').value;
  var heroChanged = false;
  if (!editImages.length) {
    document.getElementById('f-hero').value = '';
    renderHeroPreview('');
    heroChanged = true;
  } else if (editImages.indexOf(heroVal) === -1) {
    document.getElementById('f-hero').value = editImages[0];
    renderHeroPreview(editImages[0]);
    heroChanged = true;
  }

  var grid = document.getElementById('gallery-grid');
  if (grid && grid.children[index]) {
    grid.removeChild(grid.children[index]);
    syncGalleryIndices();
    if (heroChanged) {
      var newHero = document.getElementById('f-hero').value;
      var nodes = grid.children;
      for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        var isHero = node.getAttribute('data-src') === newHero;
        node.classList.toggle('is-hero', isHero);
        var badge = node.querySelector('.gallery-badge');
        if (badge) badge.style.display = isHero ? '' : 'none';
      }
    }
  } else {
    renderGallery();
  }
}

function onGalleryFilesChange(event) {
  if (!requirePermission('uploads.write', '你沒有上傳圖片的權限')) {
    event.target.value = '';
    return;
  }

  var files = event.target.files;
  if (!files || !files.length) {
    return;
  }

  var articleId = document.getElementById('f-id').value;
  if (!articleId) {
    toast('請先儲存作品再上傳圖片', true);
    event.target.value = '';
    return;
  }

  uploadFiles(articleId, files, function(paths) {
    for (var i = 0; i < paths.length; i++) {
      var fullPath = paths[i];
      if (editImages.indexOf(fullPath) === -1) {
        editImages.push(fullPath);
      }
    }

    if (!document.getElementById('f-hero').value && editImages.length) {
      document.getElementById('f-hero').value = editImages[0];
      renderHeroPreview(editImages[0]);
    }
    renderGallery();
  });

  event.target.value = '';
}

function uploadFiles(articleId, files, callback) {
  if (!requirePermission('uploads.write', '你沒有上傳圖片的權限')) {
    callback([]);
    return;
  }

  var progressEl = document.getElementById('upload-progress');
  var progressText = document.getElementById('upload-progress-text');
  var barFill = document.getElementById('upload-bar-fill');
  var formData = new FormData();
  var i;

  progressEl.classList.add('is-active');
  progressText.textContent = '上傳中... 0/' + files.length;
  barFill.style.width = '0%';

  for (i = 0; i < files.length; i++) {
    formData.append('file' + i, files[i], files[i].name);
  }

  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/upload/' + encodeURIComponent(articleId));
  if (authHeader) {
    xhr.setRequestHeader('Authorization', authHeader);
  }

  xhr.upload.onprogress = function(event) {
    if (!event.lengthComputable) {
      return;
    }
    var pct = Math.round(event.loaded / event.total * 100);
    barFill.style.width = pct + '%';
    progressText.textContent = '上傳中... ' + pct + '%';
  };

  xhr.onload = function() {
    progressEl.classList.remove('is-active');
    if (xhr.status >= 200 && xhr.status < 300) {
      var resp;
      try {
        resp = JSON.parse(xhr.responseText);
      } catch (error) {
        resp = {};
      }
      toast('已上傳 ' + ((resp.uploaded || []).length) + ' 張圖片');
      callback(resp.uploaded || []);
      return;
    }

    if (xhr.status === 401) {
      handleUnauthorized();
    }
    toast('上傳失敗：' + xhr.status, true);
    callback([]);
  };

  xhr.onerror = function() {
    progressEl.classList.remove('is-active');
    toast('上傳失敗', true);
    callback([]);
  };

  xhr.send(formData);
}

function saveArticle() {
  if (!requirePermission('articles.write', '你沒有儲存作品的權限')) {
    return;
  }

  var id = document.getElementById('f-id').value;
  var title = document.getElementById('f-title').value.replace(/^\s+|\s+$/g, '');
  if (!title) {
    toast('請輸入標題', true);
    return;
  }

  var heroImage = document.getElementById('f-hero').value.replace(/^\s+|\s+$/g, '');
  if (heroImage && editImages.indexOf(heroImage) !== 0) {
    editImages = editImages.filter(function(item) {
      return item !== heroImage;
    });
    editImages.unshift(heroImage);
  }

  var data = {
    title: title,
    description: document.getElementById('f-desc').value.replace(/^\s+|\s+$/g, ''),
    category: document.getElementById('f-category').value,
    sortOrder: parseInt(document.getElementById('f-sort').value, 10) || 99,
    featured: document.getElementById('f-featured').checked,
    featuredOrder: document.getElementById('f-featured').checked
      ? (parseInt(document.getElementById('f-featured-order').value, 10) || 1)
      : 0,
    heroImage: heroImage || (editImages[0] || ''),
    images: editImages.slice(0),
    videoId: document.getElementById('f-video').value.replace(/^\s+|\s+$/g, '') || null,
    videoVertical: document.getElementById('f-vertical').checked
  };

  if (id) {
    api('PUT', '/api/articles/' + encodeURIComponent(id), data).then(function() {
      toast('已更新：' + title);
      closeModal();
      loadArticles();
    }).catch(function(error) {
      toast('更新失敗：' + error.message, true);
    });
    return;
  }

  api('POST', '/api/articles', data).then(function(resp) {
    toast('已新增：' + title);
    if (resp && resp.id) {
      document.getElementById('f-id').value = resp.id;
    }
    closeModal();
    loadArticles();
  }).catch(function(error) {
    toast('新增失敗：' + error.message, true);
  });
}

function openConfirm(message, action) {
  confirmAction = action || null;
  document.getElementById('confirm-msg').textContent = message || '確定要執行這個動作？';
  document.getElementById('confirm-dialog').classList.add('is-open');
}

function confirmDelete(id, title) {
  if (!requirePermission('articles.delete', '你沒有刪除作品的權限')) {
    return;
  }

  openConfirm('確定要刪除「' + title + '」？', function() {
    api('DELETE', '/api/articles/' + encodeURIComponent(id)).then(function() {
      toast('已刪除');
      closeConfirm();
      loadArticles();
    }).catch(function(error) {
      toast('刪除失敗：' + error.message, true);
    });
  });
}

function closeConfirm() {
  confirmAction = null;
  document.getElementById('confirm-dialog').classList.remove('is-open');
}

function onConfirmOk() {
  if (!confirmAction) {
    closeConfirm();
    return;
  }

  var action = confirmAction;
  confirmAction = null;
  action();
}

function findAccount(username) {
  for (var i = 0; i < accountsCache.length; i++) {
    if (accountsCache[i].username === username) {
      return accountsCache[i];
    }
  }
  return null;
}

function updateAccountsSummary() {
  var enabledCount = 0;
  var managerCount = 0;

  for (var i = 0; i < accountsCache.length; i++) {
    if (accountsCache[i].enabled) {
      enabledCount += 1;
    }
    if (accountsCache[i].enabled && accountsCache[i].permissions.indexOf('accounts.manage') !== -1) {
      managerCount += 1;
    }
  }

  document.getElementById('accounts-summary').textContent =
    '共 ' + accountsCache.length + ' 個帳戶，啟用 ' + enabledCount + ' 個，具帳戶管理權限 ' + managerCount + ' 個';
}

function renderAccountsList() {
  var tbody = document.getElementById('accounts-list');
  if (!accountsCache.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-state">目前尚未建立帳戶</td></tr>';
    return;
  }

  var rows = [];
  for (var i = 0; i < accountsCache.length; i++) {
    var account = accountsCache[i];
    var classes = [];
    if (account.username === selectedAccountUsername) {
      classes.push('is-selected');
    }
    if (!account.enabled) {
      classes.push('is-disabled');
    }

    rows.push(
      '<tr class="' + classes.join(' ') + '" onclick="openAccountForm(\'' + esc(account.username) + '\')">' +
        '<td><div class="row-title"><strong>' + esc(account.username) + '</strong>' +
          (currentAccount && currentAccount.username === account.username ? '<span class="muted">目前登入</span>' : '') +
        '</div><div class="muted">' + esc(account.name || '') + '</div></td>' +
        '<td><span class="role-pill role-' + esc(account.role) + '">' + esc(roleLabel(account.role)) + '</span></td>' +
        '<td><span class="status-chip ' + (account.enabled ? 'is-enabled' : 'is-disabled') + '">' + (account.enabled ? '啟用' : '停用') + '</span></td>' +
        '<td>' + esc(permissionSummary(account.permissions)) + '</td>' +
      '</tr>'
    );
  }

  tbody.innerHTML = rows.join('');
}

function setPermissionCheckboxes(permissions) {
  var boxes = document.querySelectorAll('input[name="acc-permission"]');
  for (var i = 0; i < boxes.length; i++) {
    boxes[i].checked = permissions.indexOf(boxes[i].value) !== -1;
  }
}

function selectedPermissions() {
  var boxes = document.querySelectorAll('input[name="acc-permission"]');
  var permissions = [];
  for (var i = 0; i < boxes.length; i++) {
    if (boxes[i].checked) {
      permissions.push(boxes[i].value);
    }
  }
  return permissions;
}

function onAccountRoleChange() {
  var role = document.getElementById('acc-role').value;
  var boxes = document.querySelectorAll('input[name="acc-permission"]');
  var isCustom = role === 'custom';

  if (!isCustom) {
    setPermissionCheckboxes(ROLE_PRESETS[role] || []);
  }

  for (var i = 0; i < boxes.length; i++) {
    boxes[i].disabled = !isCustom;
  }

  document.getElementById('account-permission-note').textContent = isCustom
    ? '目前為自訂權限，可自由勾選。'
    : '目前使用「' + roleLabel(role) + '」預設權限組合。';
}

function openAccountForm(username) {
  var account = username ? findAccount(username) : null;
  selectedAccountUsername = account ? account.username : '';
  renderAccountsList();

  document.getElementById('acc-password').value = '';

  if (!account) {
    document.getElementById('account-form-title').textContent = '新增帳戶';
    document.getElementById('acc-username-original').value = '';
    document.getElementById('acc-username').value = '';
    document.getElementById('acc-username').disabled = false;
    document.getElementById('acc-name').value = '';
    document.getElementById('acc-role').value = 'viewer';
    document.getElementById('acc-enabled').checked = true;
    document.getElementById('account-delete-btn').style.display = 'none';
    setPermissionCheckboxes(ROLE_PRESETS.viewer);
    onAccountRoleChange();
    return;
  }

  document.getElementById('account-form-title').textContent = '編輯帳戶';
  document.getElementById('acc-username-original').value = account.username;
  document.getElementById('acc-username').value = account.username;
  document.getElementById('acc-username').disabled = true;
  document.getElementById('acc-name').value = account.name || '';
  document.getElementById('acc-role').value = account.role || 'viewer';
  document.getElementById('acc-enabled').checked = !!account.enabled;
  document.getElementById('account-delete-btn').style.display = '';
  document.getElementById('account-delete-btn').disabled = !!(currentAccount && currentAccount.username === account.username);
  setPermissionCheckboxes(account.permissions || []);
  onAccountRoleChange();
}

function loadAccounts(preselectUsername) {
  if (!hasPermission('accounts.manage')) {
    return Promise.resolve();
  }

  return api('GET', '/api/accounts').then(function(data) {
    accountsCache = (data && data.accounts) || [];
    updateAccountsSummary();
    renderAccountsList();

    var nextUsername = preselectUsername;
    if (!nextUsername || !findAccount(nextUsername)) {
      nextUsername = selectedAccountUsername;
    }
    if (!nextUsername || !findAccount(nextUsername)) {
      nextUsername = currentAccount ? currentAccount.username : '';
    }

    if (nextUsername && findAccount(nextUsername)) {
      openAccountForm(nextUsername);
    } else {
      openAccountForm();
    }
  }).catch(function(error) {
    toast('載入帳戶失敗：' + error.message, true);
  });
}

function openAccountsModal() {
  if (!requirePermission('accounts.manage', '只有管理員可以管理帳戶')) {
    return;
  }

  document.getElementById('accounts-modal').classList.add('is-open');
  loadAccounts();
}

function closeAccountsModal() {
  document.getElementById('accounts-modal').classList.remove('is-open');
}

function saveAccount() {
  if (!requirePermission('accounts.manage', '只有管理員可以管理帳戶')) {
    return;
  }

  var originalUsername = document.getElementById('acc-username-original').value;
  var username = document.getElementById('acc-username').value.replace(/^\s+|\s+$/g, '');
  var name = document.getElementById('acc-name').value.replace(/^\s+|\s+$/g, '');
  var role = document.getElementById('acc-role').value;
  var enabled = document.getElementById('acc-enabled').checked;
  var password = document.getElementById('acc-password').value;
  var permissions = selectedPermissions();
  var payload = {
    name: name || username,
    role: role,
    enabled: enabled,
    permissions: permissions
  };
  var isEditing = !!originalUsername;

  if (!username) {
    toast('請輸入帳號', true);
    return;
  }

  if (!isEditing) {
    if (password.length < 6) {
      toast('新增帳戶時，密碼至少需要 6 碼', true);
      return;
    }
    payload.username = username;
    payload.password = password;
  } else if (password) {
    if (password.length < 6) {
      toast('新密碼至少需要 6 碼', true);
      return;
    }
    payload.password = password;
  }

  api(isEditing ? 'PUT' : 'POST', isEditing ? '/api/accounts/' + encodeURIComponent(originalUsername) : '/api/accounts', payload)
    .then(function(response) {
      var account = response && response.account ? response.account : null;
      var targetUsername = account ? account.username : username;
      var isSelf = !!(currentAccount && targetUsername === currentAccount.username);

      if (isSelf && password) {
        toast('目前帳戶密碼已更新，請重新登入', false);
        handleUnauthorized(true);
        return;
      }

      var next = Promise.resolve();
      if (isSelf) {
        next = fetchSession({ silentUnauthorized: true });
      }

      next.then(function() {
        toast(isEditing ? '帳戶已更新' : '帳戶已新增');
        return loadAccounts(targetUsername);
      });
    })
    .catch(function(error) {
      toast('儲存帳戶失敗：' + error.message, true);
    });
}

function deleteSelectedAccount() {
  if (!requirePermission('accounts.manage', '只有管理員可以管理帳戶')) {
    return;
  }

  var username = document.getElementById('acc-username-original').value;
  if (!username) {
    toast('請先選擇要刪除的帳戶', true);
    return;
  }
  if (currentAccount && currentAccount.username === username) {
    toast('不能刪除目前登入中的帳戶', true);
    return;
  }

  openConfirm('確定要刪除帳戶「' + username + '」？', function() {
    api('DELETE', '/api/accounts/' + encodeURIComponent(username)).then(function() {
      closeConfirm();
      selectedAccountUsername = '';
      loadAccounts();
      toast('帳戶已刪除');
    }).catch(function(error) {
      toast('刪除帳戶失敗：' + error.message, true);
    });
  });
}

function toast(message, isError) {
  var el = document.getElementById('admin-toast');
  el.textContent = message;
  el.style.background = isError ? '#991b1b' : '#16a34a';
  el.classList.add('is-visible');
  setTimeout(function() {
    el.classList.remove('is-visible');
  }, 2500);
}

document.getElementById('confirm-ok').addEventListener('click', onConfirmOk);

document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    closeLightbox();
  }

  var lightbox = document.getElementById('gallery-lightbox');
  if (lightbox.classList.contains('is-open')) {
    if (event.key === 'ArrowLeft') {
      navLightbox(-1);
    }
    if (event.key === 'ArrowRight') {
      navLightbox(1);
    }
  }

  if (event.key === 'Enter' && document.getElementById('login-screen').style.display !== 'none') {
    doLogin();
  }
});

document.getElementById('login-user').addEventListener('input', resetLoginError);
document.getElementById('login-pass').addEventListener('input', resetLoginError);

restoreSession();
