const API = {
  dashboard: "/admin/api/dashboard/kpis",
  products: "/admin/api/products",
  orders: "/admin/api/orders",
  sales: "/admin/api/analytics/sales?range=30d",
  analyticsOrders: "/admin/api/analytics/orders?range=30d",
};

const ORDER_STEPS = [
  "pending",
  "confirmed",
  "packed",
  "shipped",
  "delivered",
  "cancelled",
];

const state = {
  products: [],
  orders: [],
  kpis: null,
  filteredProducts: [],
  selectedProduct: null,
  statsTargets: {
    totalListings: 0,
    activeOrders: 0,
    farmersOnline: 0,
    todayTrades: 0,
  },
  charts: {
    sales: null,
    orders: null,
  },
  sparklineCharts: [],
};

const elements = {
  topNav: document.getElementById("topNav"),
  avatarBtn: document.getElementById("avatarBtn"),
  avatarMenu: document.getElementById("avatarMenu"),
  notifyBtn: document.getElementById("notifyBtn"),
  productGrid: document.getElementById("productGrid"),
  ordersList: document.getElementById("ordersList"),
  searchInput: document.getElementById("searchInput"),
  refreshProductsBtn: document.getElementById("refreshProductsBtn"),
  statsRow: document.getElementById("statsRow"),
  toastStack: document.getElementById("toastStack"),
  negotiationDrawer: document.getElementById("negotiationDrawer"),
  closeDrawerBtn: document.getElementById("closeDrawerBtn"),
  drawerProductName: document.getElementById("drawerProductName"),
  drawerSummary: document.getElementById("drawerSummary"),
  askingPriceInput: document.getElementById("askingPriceInput"),
  counterOfferInput: document.getElementById("counterOfferInput"),
  chatThread: document.getElementById("chatThread"),
  declineOfferBtn: document.getElementById("declineOfferBtn"),
  counterOfferBtn: document.getElementById("counterOfferBtn"),
  acceptOfferBtn: document.getElementById("acceptOfferBtn"),
  paymentModal: document.getElementById("paymentModal"),
  closePaymentModalBtn: document.getElementById("closePaymentModalBtn"),
  paymentSummary: document.getElementById("paymentSummary"),
  confirmPaymentBtn: document.getElementById("confirmPaymentBtn"),
  escrowBadge: document.getElementById("escrowBadge"),
  successCheck: document.getElementById("successCheck"),
  salesChart: document.getElementById("salesChart"),
  ordersChart: document.getElementById("ordersChart"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString();
}

function formatPrice(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(amount || 0));
}

function createToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  elements.toastStack.appendChild(toast);
  window.setTimeout(() => toast.remove(), 3000);
}

async function fetchJson(url) {
  const response = await fetch(url, { credentials: "same-origin" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return data;
}

function renderProductSkeletons(count = 6) {
  elements.productGrid.innerHTML = Array.from({ length: count })
    .map(() => '<div class="skeleton product-skeleton"></div>')
    .join("");
}

function renderOrderSkeletons(count = 3) {
  elements.ordersList.innerHTML = Array.from({ length: count })
    .map(() => '<div class="skeleton order-skeleton"></div>')
    .join("");
}

function productBadge(product) {
  if (product.status === "approved") {
    return { label: "Organic", klass: "organic" };
  }
  if (product.status === "pending") {
    return { label: "Fresh", klass: "verified" };
  }
  return { label: "Surplus", klass: "surplus" };
}

function productImage(category, productName) {
  const label = `${category || "Farm"} • ${productName || "Produce"}`;
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 400'>
  <defs>
    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#D8F3DC'/>
      <stop offset='100%' stop-color='#95D5B2'/>
    </linearGradient>
  </defs>
  <rect width='600' height='400' fill='url(#g)'/>
  <path d='M0 290C120 240 220 240 320 290C430 345 520 338 600 312V400H0Z' fill='#2D6A4F' fill-opacity='0.23'/>
  <path d='M154 240C154 198 188 164 230 164C272 164 306 198 306 240' fill='none' stroke='#2D6A4F' stroke-width='10' stroke-linecap='round'/>
  <circle cx='230' cy='240' r='30' fill='#52B788'/>
  <rect x='390' y='180' width='90' height='72' rx='10' fill='#2D6A4F' fill-opacity='0.2'/>
  <path d='M435 176V140' stroke='#2D6A4F' stroke-width='8' stroke-linecap='round'/>
  <text x='32' y='360' fill='#1B4332' font-size='28' font-family='DM Sans, sans-serif'>${label}</text>
  </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function renderProducts() {
  const products = state.filteredProducts;
  if (!products.length) {
    elements.productGrid.innerHTML =
      '<div class="surface-card" style="grid-column: 1 / -1;">No products available right now.</div>';
    return;
  }

  elements.productGrid.innerHTML = products
    .map((product, index) => {
      const badge = productBadge(product);
      const surplusClass = badge.label === "Surplus" ? "surplus" : "";
      const farmName = product.seller_name || "Community Farm Group";
      const location = product.location || "Gujarat, India";

      return `
      <article class="product-card ${surplusClass}" style="animation-delay:${index * 0.1}s">
        <img class="product-image" src="${productImage(product.category, product.name)}" alt="${escapeHtml(product.name || "Product")}" />
        <div class="product-body">
          <span class="badge ${badge.klass}">${badge.label}</span>
          <h3 class="product-title">${escapeHtml(product.name || "Unnamed Product")}</h3>
          <div class="product-meta">${escapeHtml(farmName)} • ${escapeHtml(location)}</div>
          <div class="product-price">${formatPrice(product.price)}</div>
          <div class="card-actions">
            <button class="btn secondary negotiate-btn" data-product-id="${product.id}">Negotiate</button>
            <button class="btn primary order-btn" data-product-id="${product.id}">Order Now</button>
          </div>
        </div>
      </article>`;
    })
    .join("");
}

function timelineState(orderStatus, step) {
  const activeIndex = ORDER_STEPS.indexOf(orderStatus || "pending");
  const stepIndex = ORDER_STEPS.indexOf(step);
  if (stepIndex < activeIndex) return "done";
  if (stepIndex === activeIndex) return "active";
  return "pending";
}

function renderOrders() {
  state.sparklineCharts.forEach((chart) => chart.destroy());
  state.sparklineCharts = [];

  if (!state.orders.length) {
    elements.ordersList.innerHTML = '<div class="surface-card">No order records found.</div>';
    return;
  }

  const displayOrders = state.orders.slice(0, 8);

  elements.ordersList.innerHTML = displayOrders
    .map((order, index) => {
      const orderStatus = order.status || "pending";
      const steps = ["pending", "confirmed", "packed", "shipped", "delivered"];

      return `
      <article class="order-card" style="animation-delay:${index * 0.08}s">
        <div class="order-head">
          <div>
            <strong>${escapeHtml(order.order_number || "Order")}</strong>
            <div class="product-meta">${escapeHtml(order.buyer_name || "Buyer")}</div>
          </div>
          <div>
            <div class="product-price">${formatPrice(order.total_amount)}</div>
            <span class="badge ${orderStatus === "cancelled" ? "surplus" : "organic"}">${escapeHtml(orderStatus)}</span>
          </div>
        </div>
        <div class="timeline">
          ${steps
            .map((step) => {
              const statusClass = timelineState(orderStatus, step);
              return `
              <div class="tl-item ${statusClass}">
                <span class="tl-dot"></span>
                <div>
                  <div class="tl-label">${step.replace("_", " ")}</div>
                  <div class="tl-time">${formatDate(order.updated_at || order.created_at)}</div>
                </div>
              </div>`;
            })
            .join("")}
        </div>
        <div class="sparkline-wrap">
          <div class="sparkline-title">Cold chain temperature</div>
          <canvas id="sparkline-${index}" height="70"></canvas>
        </div>
      </article>`;
    })
    .join("");

  displayOrders.forEach((order, index) => drawSparkline(order, `sparkline-${index}`));
}

function seededRandom(seed) {
  let value = seed;
  return function random() {
    value = (value * 9301 + 49297) % 233280;
    return value / 233280;
  };
}

function drawSparkline(order, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;

  const seed = String(order.order_number || "ORD").split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const random = seededRandom(seed);
  const series = Array.from({ length: 12 }, () => Number((2 + random() * 6).toFixed(1)));

  const chart = new Chart(canvas, {
    type: "line",
    data: {
      labels: series.map((_, i) => `${i + 1}`),
      datasets: [
        {
          data: series,
          borderColor: "#52B788",
          borderWidth: 2,
          fill: true,
          backgroundColor: "rgba(82, 183, 136, 0.18)",
          tension: 0.38,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { display: false },
        y: { display: false },
      },
    },
  });

  state.sparklineCharts.push(chart);
}

function buildStatsTargets() {
  const kpis = state.kpis || {};
  const activeOrders = state.orders.filter(
    (order) => !["delivered", "cancelled"].includes(order.status)
  ).length;

  const today = new Date().toDateString();
  const todayTrades = state.orders.filter((order) => {
    if (!order.created_at) return false;
    return new Date(order.created_at).toDateString() === today;
  }).length;

  state.statsTargets.totalListings = Number(kpis.total_products || state.products.length || 0);
  state.statsTargets.activeOrders = Number(activeOrders || 0);
  state.statsTargets.farmersOnline = Math.round(Number(kpis.total_users || 0) * 0.6);
  state.statsTargets.todayTrades = Number(todayTrades || 0);
}

function animateCounters() {
  const counters = document.querySelectorAll("[data-counter]");
  counters.forEach((counter) => {
    const key = counter.dataset.counter;
    const target = Number(state.statsTargets[key] || 0);
    const duration = 900;
    const startTime = performance.now();

    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const value = Math.round(progress * target);
      counter.textContent = new Intl.NumberFormat("en-IN").format(value);
      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  });
}

function setupCounterObserver() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCounters();
          observer.disconnect();
        }
      });
    },
    { threshold: 0.35 }
  );

  observer.observe(elements.statsRow);
}

function setupRevealAnimations() {
  const revealItems = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12 }
  );

  revealItems.forEach((item) => observer.observe(item));
}

function openDrawer(product) {
  state.selectedProduct = product;
  elements.negotiationDrawer.classList.add("open");
  elements.negotiationDrawer.setAttribute("aria-hidden", "false");

  elements.drawerProductName.textContent = product.name || "Negotiation";
  elements.drawerSummary.innerHTML = `
    <strong>${escapeHtml(product.name || "Product")}</strong><br />
    ${escapeHtml(product.description || "Farm produce listed for direct trade.")}<br />
    Farm: ${escapeHtml(product.seller_name || "Community Farm Group")}
  `;

  elements.askingPriceInput.value = formatPrice(product.price || 0);
  elements.counterOfferInput.value = Math.max(1, Number(product.price || 100) - 200);

  const farmerText = `Current ask is ${formatPrice(product.price || 0)} for this batch.`;
  const buyerText = `Can we negotiate for faster bulk pickup?`;
  elements.chatThread.innerHTML = `
    <div class="chat-bubble farmer">${escapeHtml(farmerText)}</div>
    <div class="chat-bubble buyer">${escapeHtml(buyerText)}</div>
  `;
}

function closeDrawer() {
  elements.negotiationDrawer.classList.remove("open");
  elements.negotiationDrawer.setAttribute("aria-hidden", "true");
}

function addChatMessage(type, message) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${type}`;
  bubble.textContent = message;
  elements.chatThread.appendChild(bubble);
  elements.chatThread.scrollTop = elements.chatThread.scrollHeight;
}

function openPaymentModal(product) {
  state.selectedProduct = product;
  const subtotal = Number(product.price || 0);
  const logistics = Math.round(subtotal * 0.05);
  const total = subtotal + logistics;

  elements.paymentSummary.innerHTML = `
    <div class="summary-row"><span>Product</span><strong>${escapeHtml(product.name || "Produce")}</strong></div>
    <div class="summary-row"><span>Subtotal</span><strong>${formatPrice(subtotal)}</strong></div>
    <div class="summary-row"><span>Logistics</span><strong>${formatPrice(logistics)}</strong></div>
    <div class="summary-row"><span>Total</span><strong>${formatPrice(total)}</strong></div>
  `;

  elements.escrowBadge.textContent = "Held in Escrow";
  elements.successCheck.classList.remove("visible");
  elements.successCheck.setAttribute("aria-hidden", "true");
  elements.paymentModal.classList.add("open");
  elements.paymentModal.setAttribute("aria-hidden", "false");
}

function closePaymentModal() {
  elements.paymentModal.classList.remove("open");
  elements.paymentModal.setAttribute("aria-hidden", "true");
}

function filterProducts() {
  const query = (elements.searchInput.value || "").trim().toLowerCase();
  state.filteredProducts = state.products.filter((product) => {
    const name = String(product.name || "").toLowerCase();
    return !query || name.includes(query);
  });
  renderProducts();
}

async function loadDashboard() {
  const payload = await fetchJson(API.dashboard);
  state.kpis = payload.kpis || {};
}

async function loadProducts() {
  const payload = await fetchJson(`${API.products}?page=1&page_size=30`);
  state.products = payload.items || [];
  state.filteredProducts = [...state.products];
}

async function loadOrders() {
  const payload = await fetchJson(`${API.orders}?page=1&page_size=20`);
  state.orders = payload.items || [];
}

async function loadAnalytics() {
  const [salesPayload, ordersPayload] = await Promise.all([
    fetchJson(API.sales),
    fetchJson(API.analyticsOrders),
  ]);

  drawMainChart(
    elements.salesChart,
    "sales",
    salesPayload.series || [],
    "#2D6A4F",
    "rgba(82, 183, 136, 0.22)"
  );
  drawMainChart(
    elements.ordersChart,
    "orders",
    ordersPayload.series || [],
    "#E76F51",
    "rgba(244, 162, 97, 0.25)"
  );
}

function drawMainChart(canvas, key, series, borderColor, fillColor) {
  if (!canvas || typeof Chart === "undefined") return;
  if (state.charts[key]) {
    state.charts[key].destroy();
  }

  state.charts[key] = new Chart(canvas, {
    type: "line",
    data: {
      labels: series.map((point) => point.date),
      datasets: [
        {
          data: series.map((point) => Number(point.value || 0)),
          borderColor,
          backgroundColor: fillColor,
          fill: true,
          tension: 0.35,
          pointRadius: 0,
          borderWidth: 2.1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: "#6B7280", maxTicksLimit: 6 },
          grid: { display: false },
        },
        y: {
          ticks: { color: "#6B7280", maxTicksLimit: 5 },
          grid: { color: "rgba(107, 114, 128, 0.12)" },
        },
      },
    },
  });
}

function bindEvents() {
  window.addEventListener("scroll", () => {
    elements.topNav.classList.toggle("scrolled", window.scrollY > 8);
  });

  elements.avatarBtn.addEventListener("click", () => {
    const isOpen = elements.avatarMenu.classList.toggle("open");
    elements.avatarBtn.setAttribute("aria-expanded", String(isOpen));
  });

  window.addEventListener("click", (event) => {
    if (!elements.avatarBtn.contains(event.target) && !elements.avatarMenu.contains(event.target)) {
      elements.avatarMenu.classList.remove("open");
      elements.avatarBtn.setAttribute("aria-expanded", "false");
    }
  });

  elements.notifyBtn.addEventListener("click", () => {
    createToast("You have 3 new order alerts.", "warning");
  });

  elements.searchInput.addEventListener("input", filterProducts);
  elements.refreshProductsBtn.addEventListener("click", async () => {
    renderProductSkeletons(6);
    try {
      await loadProducts();
      filterProducts();
      createToast("Marketplace feed refreshed.", "success");
    } catch (error) {
      createToast(error.message, "error");
    }
  });

  elements.productGrid.addEventListener("click", (event) => {
    const negotiateButton = event.target.closest(".negotiate-btn");
    const orderButton = event.target.closest(".order-btn");

    if (!negotiateButton && !orderButton) return;

    const productId = (negotiateButton || orderButton).dataset.productId;
    const product = state.products.find((item) => item.id === productId);
    if (!product) return;

    if (negotiateButton) {
      openDrawer(product);
    }

    if (orderButton) {
      openPaymentModal(product);
    }
  });

  elements.closeDrawerBtn.addEventListener("click", closeDrawer);

  elements.declineOfferBtn.addEventListener("click", () => {
    addChatMessage("buyer", "I will skip this lot for now.");
    createToast("Offer declined.", "warning");
    closeDrawer();
  });

  elements.counterOfferBtn.addEventListener("click", () => {
    const counterValue = Number(elements.counterOfferInput.value || 0);
    addChatMessage("buyer", `Counter offer: ${formatPrice(counterValue)}`);
    addChatMessage("farmer", "Received. I can confirm this if pickup is today.");
    createToast("Counter-offer sent.", "success");
  });

  elements.acceptOfferBtn.addEventListener("click", () => {
    addChatMessage("buyer", "Accepted. Please lock this quantity.");
    createToast("Offer accepted.", "success");
    closeDrawer();
  });

  elements.closePaymentModalBtn.addEventListener("click", closePaymentModal);

  elements.confirmPaymentBtn.addEventListener("click", () => {
    elements.confirmPaymentBtn.disabled = true;
    elements.confirmPaymentBtn.textContent = "Processing...";
    setTimeout(() => {
      elements.successCheck.classList.add("visible");
      elements.successCheck.setAttribute("aria-hidden", "false");
      elements.escrowBadge.textContent = "Released to Farmer";
      elements.confirmPaymentBtn.disabled = false;
      elements.confirmPaymentBtn.textContent = "Pay Now";
      createToast("Payment completed and escrow released.", "success");
    }, 1000);
  });

  elements.paymentModal.addEventListener("click", (event) => {
    if (event.target === elements.paymentModal) {
      closePaymentModal();
    }
  });
}

async function initialize() {
  renderProductSkeletons();
  renderOrderSkeletons();
  bindEvents();
  setupRevealAnimations();
  setupCounterObserver();

  try {
    await Promise.all([loadDashboard(), loadProducts(), loadOrders(), loadAnalytics()]);

    buildStatsTargets();
    filterProducts();
    renderOrders();
    createToast("Live marketplace data loaded.", "success");
  } catch (error) {
    elements.productGrid.innerHTML = '<div class="surface-card" style="grid-column: 1 / -1;">Unable to load products. Please ensure backend session is active.</div>';
    elements.ordersList.innerHTML = '<div class="surface-card">Unable to load orders data.</div>';
    createToast(error.message, "error");
  }
}

initialize();
