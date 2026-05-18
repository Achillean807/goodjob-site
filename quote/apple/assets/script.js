
document.addEventListener('click', (e)=>{
  const tab=e.target.closest('[data-tab]');
  if(tab){
    const group=tab.closest('.moduleTabs').dataset.group;
    document.querySelectorAll(`.moduleTabs[data-group="${group}"] .tab`).forEach(t=>t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll(`[data-panel-group="${group}"]`).forEach(p=>p.classList.remove('active'));
    document.querySelector(`[data-panel-group="${group}"][data-panel="${tab.dataset.tab}"]`)?.classList.add('active');
  }
  const copy=e.target.closest('[data-copy]');
  if(copy){
    const box=copy.closest('.promptBox').querySelector('pre').innerText;
    navigator.clipboard.writeText(box).then(()=>{copy.textContent='已複製'; setTimeout(()=>copy.textContent='複製',1200)})
  }
});
