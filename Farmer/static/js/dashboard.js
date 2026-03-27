/* ── dashboard.js ── */
const FARMER_NAME = document.getElementById('farmerName')?.textContent || 'Farmer';

// ── Toast ──────────────────────────────────────────────────────────
function toast(msg, type='success') {
  const icons = { success:'✓', error:'✕', warning:'⚠' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${icons[type]}</span> ${msg}`;
  document.getElementById('toastContainer').appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// ── Nav active tab ─────────────────────────────────────────────────
document.querySelectorAll('.nav-item[data-section]').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');
    const sec = item.dataset.section;
    document.querySelectorAll('.section[data-id]').forEach(s => {
      s.style.display = (sec === 'all' || s.dataset.id === sec) ? '' : 'none';
    });
    if (window.innerWidth <= 900) closeSidebar();
  });
});

// ── Mobile sidebar ─────────────────────────────────────────────────
function openSidebar()  { document.getElementById('sidebar').classList.add('open'); document.getElementById('overlay').classList.add('show'); }
function closeSidebar() { document.getElementById('sidebar').classList.remove('open'); document.getElementById('overlay').classList.remove('show'); }
document.getElementById('hamburger')?.addEventListener('click', openSidebar);
document.getElementById('overlay')?.addEventListener('click', closeSidebar);

// ── Mark as Sold ───────────────────────────────────────────────────
document.querySelectorAll('.btn-sold').forEach(btn => {
  btn.addEventListener('click', () => {
    const card = btn.closest('.listing-card');
    const badge = card.querySelector('.status-badge');
    badge.className = 'status-badge status-sold';
    badge.textContent = 'Sold';
    btn.disabled = true; btn.style.opacity = '.5';
    toast('Product marked as sold');
  });
});

// ── Delete listing ─────────────────────────────────────────────────
document.querySelectorAll('.btn-delete').forEach(btn => {
  btn.addEventListener('click', () => {
    if (!confirm('Remove this listing?')) return;
    const card = btn.closest('.listing-card');
    card.classList.add('removing');
    setTimeout(() => { card.remove(); updateSummary(); }, 300);
    toast('Listing removed', 'warning');
  });
});

// ── Offers: Accept ─────────────────────────────────────────────────
document.querySelectorAll('.btn-accept').forEach(btn => {
  btn.addEventListener('click', () => {
    const card = btn.closest('.offer-card');
    const buyer = card.querySelector('.buyer-name').textContent;
    card.classList.add('removing');
    setTimeout(() => { card.remove(); updateOfferBadge(); }, 300);
    toast(`Offer from ${buyer} accepted!`);
  });
});

// ── Offers: Reject ─────────────────────────────────────────────────
document.querySelectorAll('.btn-reject').forEach(btn => {
  btn.addEventListener('click', () => {
    const card = btn.closest('.offer-card');
    const buyer = card.querySelector('.buyer-name').textContent;
    card.classList.add('removing');
    setTimeout(() => { card.remove(); updateOfferBadge(); }, 300);
    toast(`Offer from ${buyer} rejected`, 'warning');
  });
});

// ── Offers: Counter ────────────────────────────────────────────────
document.querySelectorAll('.btn-counter').forEach(btn => {
  btn.addEventListener('click', () => {
    const box = btn.closest('.offer-actions').nextElementSibling;
    box.classList.toggle('show');
    if (box.classList.contains('show')) {
      box.querySelector('input').focus();
      btn.textContent = '✕ Cancel';
    } else {
      btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5h2M12 5v14M5 12h14"/></svg> Counter Offer`;
    }
  });
});
document.querySelectorAll('.btn-send-counter').forEach(btn => {
  btn.addEventListener('click', () => {
    const box = btn.closest('.counter-input-box');
    const val = box.querySelector('input').value;
    if (!val || isNaN(val) || val <= 0) { toast('Enter a valid price', 'error'); return; }
    const card = btn.closest('.offer-card');
    const buyer = card.querySelector('.buyer-name').textContent;
    card.classList.add('removing');
    setTimeout(() => { card.remove(); updateOfferBadge(); }, 300);
    toast(`Counter offer of ₹${val}/kg sent to ${buyer}`);
  });
});

// ── Update offer badge count ───────────────────────────────────────
function updateOfferBadge() {
  const count = document.querySelectorAll('.offer-card').length;
  const badge = document.querySelector('.nav-badge');
  if (badge) badge.textContent = count > 0 ? count : '';
  const summaryOffers = document.getElementById('summaryOffers');
  if (summaryOffers) { flashNum(summaryOffers, count); }
}

// ── Order status update ────────────────────────────────────────────
document.querySelectorAll('.btn-update-status').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const dd = btn.nextElementSibling;
    document.querySelectorAll('.status-dropdown.open').forEach(d => { if (d !== dd) d.classList.remove('open'); });
    dd.classList.toggle('open');
  });
});
document.querySelectorAll('.status-option').forEach(opt => {
  opt.addEventListener('click', () => {
    const card = opt.closest('.order-card');
    const statusMap = { pending:'pending', accepted:'accepted', shipped:'shipped', delivered:'delivered' };
    const val = opt.dataset.val;
    const steps = card.querySelectorAll('.progress-step');
    const lines = card.querySelectorAll('.progress-line');
    const order = ['pending','accepted','shipped','delivered'];
    const idx = order.indexOf(val);
    steps.forEach((s, i) => {
      s.classList.remove('done','active');
      if (i < idx) s.classList.add('done');
      if (i === idx) s.classList.add('active');
    });
    lines.forEach((l, i) => { l.classList.toggle('done', i < idx); });
    const dd = opt.closest('.status-dropdown');
    dd.classList.remove('open');
    toast(`Order status → ${val}`);
  });
});
document.addEventListener('click', () => {
  document.querySelectorAll('.status-dropdown.open').forEach(d => d.classList.remove('open'));
});

// ── Summary live update ────────────────────────────────────────────
function updateSummary() {
  const count = document.querySelectorAll('.listing-card').length;
  const el = document.getElementById('summaryProducts');
  if (el) flashNum(el, count);
}
function flashNum(el, n) {
  el.style.transform = 'scale(1.3)'; el.style.opacity = '.5';
  setTimeout(() => { el.textContent = n; el.style.transform = 'scale(1)'; el.style.opacity = '1'; }, 150);
}

// ── Bar chart animation ────────────────────────────────────────────
document.querySelectorAll('.bar[data-h]').forEach(bar => {
  bar.style.height = '0';
  setTimeout(() => { bar.style.height = bar.dataset.h; bar.style.transition = 'height .6s cubic-bezier(.4,0,.2,1)'; }, 300);
});

// ── Close dropdowns on outside click ──────────────────────────────
document.getElementById('overlay')?.addEventListener('click', () => {
  document.querySelectorAll('.status-dropdown').forEach(d => d.classList.remove('open'));
});
