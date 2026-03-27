(function () {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content || '';

  const escapeHtml = (value) => String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  async function apiFetch(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const headers = {
      ...(options.headers || {}),
    };

    if (!headers['Content-Type'] && options.body) {
      headers['Content-Type'] = 'application/json';
    }

    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      headers['X-CSRFToken'] = csrfToken();
    }

    const response = await fetch(url, { ...options, headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || 'Request failed');
    }
    return payload;
  }

  function notify(message, type = 'info') {
    const panel = document.createElement('div');
    panel.className = [
      'fixed right-4 top-4 z-50 rounded-lg px-4 py-3 text-sm shadow-lg',
      type === 'success' ? 'bg-emerald-600 text-white' : '',
      type === 'error' ? 'bg-rose-600 text-white' : '',
      type === 'info' ? 'bg-slate-900 text-white' : '',
    ].join(' ');
    panel.textContent = message;
    document.body.appendChild(panel);
    setTimeout(() => panel.remove(), 2400);
  }

  function formatCurrency(amount) {
    const numeric = Number(amount || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(numeric);
  }

  function formatDate(value) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString();
  }

  function renderPagination(containerId, meta, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!meta || (meta.total_pages || 0) <= 1) {
      container.innerHTML = '';
      return;
    }

    const prevDisabled = !meta.has_prev ? 'disabled opacity-50 cursor-not-allowed' : '';
    const nextDisabled = !meta.has_next ? 'disabled opacity-50 cursor-not-allowed' : '';

    container.innerHTML = `
      <button class="prev-page rounded border border-slate-300 px-3 py-1.5 text-sm ${prevDisabled}">Prev</button>
      <span class="text-sm text-slate-600">Page ${meta.page} of ${meta.total_pages}</span>
      <button class="next-page rounded border border-slate-300 px-3 py-1.5 text-sm ${nextDisabled}">Next</button>
    `;

    const prevButton = container.querySelector('.prev-page');
    const nextButton = container.querySelector('.next-page');

    prevButton?.addEventListener('click', () => {
      if (meta.has_prev) onPageChange(meta.page - 1);
    });

    nextButton?.addEventListener('click', () => {
      if (meta.has_next) onPageChange(meta.page + 1);
    });
  }

  function renderBarChart(containerId, series, formatValue) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!series.length) {
      container.innerHTML = '<p class="text-sm text-slate-500">No data</p>';
      return;
    }

    const maxValue = Math.max(...series.map((point) => Number(point.value || 0)), 1);
    const sampled = series.length > 24 ? series.filter((_, idx) => idx % Math.ceil(series.length / 24) === 0) : series;

    container.innerHTML = `<div class="flex h-52 items-end gap-1">${sampled.map((point) => {
      const value = Number(point.value || 0);
      const height = Math.max(6, Math.round((value / maxValue) * 180));
      return `<div class="group relative flex-1 rounded-t bg-brand-600/80" style="height:${height}px">
        <span class="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 rounded bg-slate-900 px-2 py-1 text-xs text-white opacity-0 group-hover:opacity-100">${escapeHtml(formatValue(value))}</span>
      </div>`;
    }).join('')}</div>
    <div class="mt-2 flex justify-between text-xs text-slate-500">
      <span>${sampled[0]?.date || ''}</span>
      <span>${sampled[sampled.length - 1]?.date || ''}</span>
    </div>`;
  }

  window.AdminApp = {
    apiFetch,
    notify,
    formatCurrency,
    formatDate,
    renderPagination,
    renderBarChart,
    escapeHtml,
  };
})();
