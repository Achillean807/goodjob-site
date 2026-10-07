(function () {
  'use strict';
  var field = document.getElementById('party-inquiry');
  var button = document.getElementById('party-inquiry-copy');
  var status = document.getElementById('party-inquiry-status');
  if (!field || !button || !status) return;

  function selectForCopy() {
    field.focus();
    field.select();
    field.setSelectionRange(0, field.value.length);
    status.textContent = '已選取清單，請長按或使用複製，再貼到 LINE。';
  }

  button.addEventListener('click', function () {
    if (!field.value.trim()) {
      status.textContent = '請先填入活動需求；尚未決定的項目可寫「未定」。';
      field.focus();
      return;
    }
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      selectForCopy();
      return;
    }
    navigator.clipboard.writeText(field.value).then(function () {
      status.textContent = '已複製，開啟 LINE 後貼上即可。';
    }).catch(selectForCopy);
  });
})();
