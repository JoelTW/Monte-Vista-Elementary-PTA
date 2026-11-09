// Mobile menu and dropdowns
const menuBtn = document.querySelector('.menu-btn'), nav = document.getElementById('nav');
menuBtn.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  menuBtn.setAttribute('aria-expanded', open);
});
document.querySelectorAll('.dd-btn').forEach(btn => btn.addEventListener('click', () => {
  const li = btn.parentElement, open = li.classList.toggle('open');
  btn.setAttribute('aria-expanded', open);
}));

// Pop-up dialogs (e.g. the President's full message)
document.querySelectorAll('[data-dialog-open]').forEach(btn => btn.addEventListener('click', () => {
  document.getElementById(btn.dataset.dialogOpen).showModal();
}));
document.querySelectorAll('dialog').forEach(dlg => {
  dlg.querySelectorAll('[data-dialog-close]').forEach(b => b.addEventListener('click', () => dlg.close()));
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });   // click on the dark backdrop closes it
});
