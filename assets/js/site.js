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
