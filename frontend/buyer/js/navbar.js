(function () {
  "use strict";

  const NAV_ITEMS = [
    { href: "index.html", key: "marketplace", icon: "store", label: "Marketplace" },
    { href: "map.html", key: "map", icon: "map", label: "Map" },
    { href: "wishlist.html", key: "wishlist", icon: "heart", label: "Wishlist" },
    { href: "orders.html", key: "orders", icon: "package", label: "My Orders" },
    { href: "negotiations.html", key: "negotiations", icon: "handshake", label: "Negotiations" },
  ];

  const SEARCH_HINTS = ["Tomato", "Onion", "Wheat", "Rice", "Mango", "Barley", "Cotton", "Potato", "Turmeric", "Spinach"];

  function getCurrentPage() {
    return window.location.pathname.split("/").pop() || "index.html";
  }

  function isActivePage(href, currentPage) {
    if (href === "index.html" && currentPage === "") return true;
    return href === currentPage;
  }

  function renderLinks(currentPage) {
    return NAV_ITEMS
      .map((item) => {
        const active = isActivePage(item.href, currentPage) ? "active" : "";
        return `<li><a href="${item.href}" class="${active}" data-page="${item.key}"><i data-lucide="${item.icon}"></i>${item.label}</a></li>`;
      })
      .join("");
  }

  function renderMobileLinks(currentPage) {
    return NAV_ITEMS
      .map((item) => {
        const active = isActivePage(item.href, currentPage) ? "active" : "";
        return `<a href="${item.href}" class="${active}"><i data-lucide="${item.icon}"></i>${item.label}</a>`;
      })
      .join("");
  }

  function getLeafLogoSvg() {
    return `
      <svg class="nav-logo-svg" viewBox="0 0 28 28" fill="none" aria-hidden="true">
        <path d="M4 24C4 24 8 10 20 6C20 6 22 16 14 20C10 22 4 24 4 24Z" fill="#4ade80" stroke="#166534" stroke-width="1.5"></path>
        <line x1="4" y1="24" x2="14" y2="14" stroke="#166534" stroke-width="1.5" stroke-linecap="round"></line>
      </svg>
    `;
  }

  function createNavbar() {
    const header = document.querySelector("header");
    if (!header) return;
    header.classList.add("kc-navbar-host");

    const currentPage = getCurrentPage();
    const user = JSON.parse(localStorage.getItem("user") || "null");
    const initials = String(user?.name || "Guest").charAt(0).toUpperCase();

    header.innerHTML = `
      <nav class="kc-navbar" id="navbar">
        <div class="nav-inner">
          <a href="index.html" class="nav-logo">
            ${getLeafLogoSvg()}
            <span class="logo-text">Krishi<strong>Connect</strong></span>
          </a>

          <div class="nav-search">
            <div class="search-wrapper">
              <i data-lucide="search" class="search-icon"></i>
              <input type="text" id="navSearch" placeholder="Search vegetables, fruits, grains..." autocomplete="off">
              <button class="search-btn" type="button" id="navSearchBtn">Search</button>
            </div>
            <div class="search-dropdown" id="searchDropdown"></div>
          </div>

          <ul class="nav-links">${renderLinks(currentPage)}</ul>

          <div class="nav-actions">
            <a href="cart.html" class="cart-btn cart-icon" aria-label="Cart">
              <i data-lucide="shopping-cart"></i>
              <span class="cart-badge" id="cart-badge">0</span>
            </a>

            ${user ? `
              <div class="user-menu" id="userMenu">
                <button class="avatar-btn" id="avatarBtn" type="button" aria-label="Open user menu">
                  <span class="avatar-initials" id="avatarInitials">${initials}</span>
                </button>
                <div class="user-dropdown glass-strong" id="userDropdown">
                  <div class="dropdown-header">
                    <div class="dropdown-avatar">${initials}</div>
                    <div>
                      <div class="dropdown-name" id="dropdownName">${user?.name || "User"}</div>
                      <div class="dropdown-email" id="dropdownEmail">${user?.email || "No email"}</div>
                    </div>
                  </div>
                  <div class="dropdown-divider"></div>
                  <a href="profile.html" class="dropdown-item"><i data-lucide="user"></i>My Profile</a>
                  <a href="orders.html" class="dropdown-item"><i data-lucide="package"></i>My Orders</a>
                  <a href="wishlist.html" class="dropdown-item"><i data-lucide="heart"></i>Wishlist</a>
                  <div class="dropdown-divider"></div>
                  <button class="dropdown-item danger" type="button" id="navbarLogoutBtn"><i data-lucide="log-out"></i>Logout</button>
                </div>
              </div>
            ` : `<a href="login.html" class="auth-link" id="auth-link"><i data-lucide="log-in"></i>Sign In</a>`}

            <button class="hamburger" id="hamburger" type="button" aria-label="Toggle mobile menu">
              <i data-lucide="menu" id="hamburgerIcon"></i>
            </button>
          </div>
        </div>

        <div class="mobile-menu glass" id="mobileMenu">
          <div class="mobile-search">
            <i data-lucide="search"></i>
            <input type="text" id="mobileNavSearch" placeholder="Search products...">
          </div>
          ${renderMobileLinks(currentPage)}
          <a href="cart.html" class="cart-icon"><i data-lucide="shopping-cart"></i>Cart<span class="cart-badge" id="mobile-cart-badge">0</span></a>
          ${user ? `<a href="profile.html"><i data-lucide="user"></i>Profile</a><button class="dropdown-item danger" type="button" id="mobileLogoutBtn"><i data-lucide="log-out"></i>Logout</button>` : `<a href="login.html"><i data-lucide="log-in"></i>Sign In</a>`}
        </div>
      </nav>
    `;

    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  function initSearch() {
    const navSearch = document.getElementById("navSearch");
    const navSearchBtn = document.getElementById("navSearchBtn");
    const dropdown = document.getElementById("searchDropdown");
    const mobileSearch = document.getElementById("mobileNavSearch");

    if (!navSearch || !dropdown) return;

    function goSearch(value) {
      const query = encodeURIComponent(String(value || "").trim());
      window.location.href = query ? `index.html?search=${query}` : "index.html";
    }

    function renderSuggestions(value) {
      const query = String(value || "").trim().toLowerCase();
      if (!query) {
        dropdown.innerHTML = "";
        dropdown.classList.remove("show");
        return;
      }

      const matches = SEARCH_HINTS.filter((item) => item.toLowerCase().includes(query)).slice(0, 6);
      if (!matches.length) {
        dropdown.innerHTML = "";
        dropdown.classList.remove("show");
        return;
      }

      dropdown.innerHTML = matches.map((item) => `<button type="button" class="search-item">${item}</button>`).join("");
      dropdown.classList.add("show");
    }

    navSearch.addEventListener("input", () => renderSuggestions(navSearch.value));
    navSearch.addEventListener("focus", () => renderSuggestions(navSearch.value));
    navSearch.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        goSearch(navSearch.value);
      }
    });

    navSearchBtn?.addEventListener("click", () => goSearch(navSearch.value));
    mobileSearch?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        goSearch(mobileSearch.value);
      }
    });

    dropdown.addEventListener("click", (event) => {
      const item = event.target.closest(".search-item");
      if (!item) return;
      navSearch.value = item.textContent || "";
      goSearch(navSearch.value);
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".nav-search")) {
        dropdown.classList.remove("show");
      }
    });
  }

  function initInteractions() {
    const navbar = document.getElementById("navbar");
    const hamburger = document.getElementById("hamburger");
    const mobileMenu = document.getElementById("mobileMenu");
    const avatarBtn = document.getElementById("avatarBtn");
    const userDropdown = document.getElementById("userDropdown");

    function onScroll() {
      if (!navbar) return;
      navbar.classList.toggle("scrolled", window.scrollY > 10);
    }

    function closeMenus() {
      mobileMenu?.classList.remove("open");
      userDropdown?.classList.remove("show");
    }

    window.addEventListener("scroll", onScroll);
    onScroll();

    hamburger?.addEventListener("click", (event) => {
      event.stopPropagation();
      mobileMenu?.classList.toggle("open");
    });

    avatarBtn?.addEventListener("click", (event) => {
      event.stopPropagation();
      userDropdown?.classList.toggle("show");
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest("#userMenu")) {
        userDropdown?.classList.remove("show");
      }
      if (!event.target.closest("#mobileMenu") && !event.target.closest("#hamburger")) {
        mobileMenu?.classList.remove("open");
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenus();
    });

    const logoutButtons = [document.getElementById("navbarLogoutBtn"), document.getElementById("mobileLogoutBtn")];
    logoutButtons.forEach((btn) => {
      btn?.addEventListener("click", () => {
        if (typeof window.logout === "function") {
          window.logout();
          return;
        }
        localStorage.removeItem("user");
        window.location.href = "login.html";
      });
    });
  }

  function mountNavbar() {
    createNavbar();
    initSearch();
    initInteractions();
  }

  document.addEventListener("DOMContentLoaded", mountNavbar);
})();


