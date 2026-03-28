const API_BASE = "/api";

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

// 🔐 Authentication Handlers
function signupHandler(e) {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch(`${API_BASE}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) showToast(data.error, "error");
        else {
            showToast("Signup successful! Redirecting...", "success");
            setTimeout(() => window.location.href = "login.html", 1500);
        }
    });
}

function loginHandler(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) showToast(data.error, "error");
        else {
            localStorage.setItem("user", JSON.stringify(data.user));
            showToast("Login successful!", "success");
            setTimeout(() => window.location.href = "index.html", 1000);
        }
    });
}

function logout() {
    localStorage.removeItem("user");
    window.location.reload();
}

function getNavIconSvg(name, className = "nav-icon") {
    const icons = {
        marketplace: '<path d="M3 7h18l-2 12H5L3 7z"></path><path d="M8 7V5a4 4 0 0 1 8 0v2"></path>',
        map: '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6z"></path><path d="M9 4v14"></path><path d="M15 6v14"></path>',
        heart: '<path d="M12 21s-7-4.4-9-8.9C1.4 8.5 4 5 7.6 5c1.9 0 3.3.9 4.4 2.3C13.1 5.9 14.5 5 16.4 5 20 5 22.6 8.5 21 12.1 19 16.6 12 21 12 21z"></path>',
        box: '<path d="M3 8l9-5 9 5-9 5-9-5z"></path><path d="M3 8v8l9 5 9-5V8"></path><path d="M12 13v8"></path>',
        handshake: '<path d="M9 12l3 3 3-3"></path><path d="M4 9l3-3 3 3"></path><path d="M20 9l-3-3-3 3"></path><path d="M4 15l3 3 3-3"></path>',
        user: '<circle cx="12" cy="8" r="4"></circle><path d="M4 20a8 8 0 0 1 16 0"></path>',
        logout: '<path d="M10 17l-5-5 5-5"></path><path d="M5 12h10"></path><path d="M15 5h4v14h-4"></path>',
        login: '<path d="M14 17l5-5-5-5"></path><path d="M19 12H9"></path><path d="M9 5H5v14h4"></path>',
        cart: '<circle cx="9" cy="20" r="1.5"></circle><circle cx="17" cy="20" r="1.5"></circle><path d="M3 4h2l2.2 10.5a1 1 0 0 0 1 .8h8.8a1 1 0 0 0 1-.8L20 7H7"></path>',
        search: '<circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path>',
        leaf: '<path d="M5 19c8 0 14-6 14-14C11 5 5 11 5 19z"></path><path d="M8 16c2-2 4-4 7-6"></path>'
    };
    const body = icons[name] || icons.marketplace;
    return `<svg class="${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
}

function buildNavbarLinksHtml(currentPath = "") {
    const links = [
        { href: "index.html", icon: "marketplace", label: "Marketplace" },
        { href: "map.html", icon: "map", label: "Map" },
        { href: "wishlist.html", icon: "heart", label: "Wishlist" },
        { href: "orders.html", icon: "box", label: "My Orders" },
        { href: "negotiations.html", icon: "handshake", label: "My Negotiations" },
    ];
    return links
        .map(item => {
            const activeClass = currentPath === item.href ? "active" : "";
            return `<a href="${item.href}" class="${activeClass}">${getNavIconSvg(item.icon)}<span>${item.label}</span></a>`;
        })
        .join("");
}

function initNavbarSearchSuggestions(inputElement) {
    if (!inputElement) return;

    const suggestions = [
        "Tomato", "Onion", "Wheat", "Rice", "Mango", "Barley", "Cotton", "Potato", "Turmeric", "Spinach"
    ];

    const wrapper = inputElement.closest('.search-bar') || inputElement.parentElement;
    if (!wrapper || wrapper.querySelector('.search-suggestions')) return;

    const dropdown = document.createElement('div');
    dropdown.className = 'search-suggestions';
    wrapper.appendChild(dropdown);

    const render = (value) => {
        const query = String(value || '').trim().toLowerCase();
        if (!query) {
            dropdown.innerHTML = '';
            dropdown.classList.remove('show');
            return;
        }
        const filtered = suggestions.filter(item => item.toLowerCase().includes(query)).slice(0, 6);
        if (!filtered.length) {
            dropdown.innerHTML = '';
            dropdown.classList.remove('show');
            return;
        }
        dropdown.innerHTML = filtered
            .map(item => `<button type="button" class="search-suggestion-item">${escapeHtml(item)}</button>`)
            .join('');
        dropdown.classList.add('show');
    };

    inputElement.addEventListener('focus', () => render(inputElement.value));
    inputElement.addEventListener('input', () => render(inputElement.value));
    dropdown.addEventListener('click', (event) => {
        const btn = event.target.closest('.search-suggestion-item');
        if (!btn) return;
        inputElement.value = btn.innerText;
        dropdown.classList.remove('show');
        if (typeof applyFilters === 'function') applyFilters();
    });

    document.addEventListener('click', (event) => {
        if (!wrapper.contains(event.target)) {
            dropdown.classList.remove('show');
        }
    });
}

function initBuyerNavbar() {
    if (document.querySelector('.kc-navbar')) return;

    const header = document.querySelector('header');
    const navContainer = header?.querySelector('.nav-container');
    if (!header || !navContainer) return;

    header.classList.add('buyer-navbar');
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';

    let searchBar = navContainer.querySelector('.search-bar');
    if (!searchBar) {
        searchBar = document.createElement('div');
        searchBar.className = 'search-bar navbar-auto-search';
        searchBar.innerHTML = `
            <input type="text" placeholder="Search crops..." aria-label="Search crops">
            <button type="button" aria-label="Search crops">${getNavIconSvg('search', 'nav-icon nav-icon-sm')}</button>
        `;
        const navRef = navContainer.querySelector('.nav-links');
        if (navRef) navContainer.insertBefore(searchBar, navRef);

        const autoInput = searchBar.querySelector('input');
        const autoButton = searchBar.querySelector('button');
        const goToMarketplace = () => {
            const q = encodeURIComponent((autoInput?.value || '').trim());
            window.location.href = q ? `index.html?search=${q}` : 'index.html';
        };
        autoButton?.addEventListener('click', goToMarketplace);
        autoInput?.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                goToMarketplace();
            }
        });
    }

    const nav = navContainer.querySelector('.nav-links');
    if (nav) {
        const navMeta = {
            'index.html': { icon: 'marketplace', label: 'Marketplace' },
            'map.html': { icon: 'map', label: 'Map' },
            'wishlist.html': { icon: 'heart', label: 'Wishlist' },
            'orders.html': { icon: 'box', label: 'My Orders' },
            'negotiations.html': { icon: 'handshake', label: 'My Negotiations' },
        };
        const anchors = nav.querySelectorAll('a:not(.cart-icon)');
        anchors.forEach(anchor => {
            const href = anchor.getAttribute('href') || '';
            const meta = navMeta[href];
            if (meta) {
                anchor.innerHTML = `${getNavIconSvg(meta.icon)}<span>${meta.label}</span>`;
            }
            if (href === currentPath) anchor.classList.add('active');
        });

        const cartLink = nav.querySelector('a.cart-icon');
        if (cartLink) {
            const badge = cartLink.querySelector('.cart-badge');
            const badgeId = badge?.id || 'cart-badge';
            const badgeValue = (badge?.innerText || '0').trim();
            cartLink.innerHTML = `${getNavIconSvg('cart')}<span class="cart-label">Cart</span><span class="cart-badge" id="${badgeId}">${escapeHtml(badgeValue)}</span>`;
        }
    }

    const logo = navContainer.querySelector('.logo');
    if (logo && !logo.querySelector('.logo-leaf')) {
        const leaf = document.createElement('span');
        leaf.className = 'logo-leaf';
        leaf.innerHTML = getNavIconSvg('leaf');
        logo.insertBefore(leaf, logo.firstChild);
    }

    const searchInput = navContainer.querySelector('.search-bar input');
    initNavbarSearchSuggestions(searchInput);

    const authLink = document.getElementById('auth-link');
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (authLink && user) {
        const initial = String(user.name || 'U').charAt(0).toUpperCase();
        authLink.innerHTML = `
            <div class="navbar-user-menu" id="navbar-user-menu">
                <button type="button" id="navbar-user-trigger" class="navbar-avatar" title="${escapeHtml(user.name)} Profile">
                    ${escapeHtml(initial)}
                </button>
                <div id="navbar-user-dropdown" class="navbar-user-dropdown" aria-hidden="true">
                    <a href="profile.html">${getNavIconSvg('user', 'nav-icon nav-icon-sm')}<span>My Profile</span></a>
                    <a href="orders.html">${getNavIconSvg('box', 'nav-icon nav-icon-sm')}<span>My Orders</span></a>
                    <a href="wishlist.html">${getNavIconSvg('heart', 'nav-icon nav-icon-sm')}<span>Wishlist</span></a>
                    <button type="button" id="navbar-logout-btn">${getNavIconSvg('logout', 'nav-icon nav-icon-sm')}<span>Logout</span></button>
                </div>
            </div>
        `;

        const trigger = document.getElementById('navbar-user-trigger');
        const dropdown = document.getElementById('navbar-user-dropdown');
        const logoutBtn = document.getElementById('navbar-logout-btn');

        const closeDropdown = () => {
            if (!dropdown) return;
            dropdown.classList.remove('show');
            dropdown.setAttribute('aria-hidden', 'true');
        };

        trigger?.addEventListener('click', (event) => {
            event.stopPropagation();
            if (!dropdown) return;
            const next = !dropdown.classList.contains('show');
            dropdown.classList.toggle('show', next);
            dropdown.setAttribute('aria-hidden', next ? 'false' : 'true');
        });

        logoutBtn?.addEventListener('click', () => logout());

        document.addEventListener('click', (event) => {
            if (!event.target.closest('#navbar-user-menu')) closeDropdown();
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') closeDropdown();
        });
    }

    if (!navContainer.querySelector('.nav-hamburger')) {
        const hamburger = document.createElement('button');
        hamburger.type = 'button';
        hamburger.className = 'nav-hamburger';
        hamburger.setAttribute('aria-label', 'Toggle navigation menu');
        hamburger.innerHTML = '<span></span><span></span><span></span>';
        navContainer.appendChild(hamburger);

        const mobileMenu = document.createElement('div');
        mobileMenu.className = 'mobile-nav-menu';
        const mobileSearch = `
            <form class="mobile-search" onsubmit="event.preventDefault(); window.location.href='index.html';">
                <input type="text" placeholder="Search crops..." aria-label="Search crops">
                <button type="submit" aria-label="Search crops">${getNavIconSvg('search', 'nav-icon nav-icon-sm')}</button>
            </form>
        `;
        mobileMenu.innerHTML = `
            ${mobileSearch}
            <nav class="mobile-nav-links">${buildNavbarLinksHtml(currentPath)}</nav>
            <div class="mobile-nav-footer">
                <a href="cart.html" class="cart-icon">${getNavIconSvg('cart', 'nav-icon nav-icon-sm')}<span>Cart</span><span class="cart-badge" id="mobile-cart-badge">0</span></a>
            </div>
        `;

        const footer = mobileMenu.querySelector('.mobile-nav-footer');
        if (user) {
            footer.insertAdjacentHTML('beforeend', `<a href="profile.html">${getNavIconSvg('user', 'nav-icon nav-icon-sm')}<span>My Profile</span></a><button type="button" id="mobile-logout-btn">${getNavIconSvg('logout', 'nav-icon nav-icon-sm')}<span>Logout</span></button>`);
        } else {
            footer.insertAdjacentHTML('beforeend', `<a href="login.html">${getNavIconSvg('login', 'nav-icon nav-icon-sm')}<span>Sign In</span></a>`);
        }

        header.appendChild(mobileMenu);

        const toggleMobile = () => {
            const opening = !mobileMenu.classList.contains('open');
            mobileMenu.classList.toggle('open', opening);
            hamburger.classList.toggle('open', opening);
        };
        hamburger.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleMobile();
        });

        document.getElementById('mobile-logout-btn')?.addEventListener('click', () => logout());

        document.addEventListener('click', (event) => {
            if (!mobileMenu.contains(event.target) && !hamburger.contains(event.target)) {
                mobileMenu.classList.remove('open');
                hamburger.classList.remove('open');
            }
        });
    }

    const onScroll = () => {
        if (window.scrollY > 10) {
            header.style.backdropFilter = 'blur(12px)';
            header.style.background = 'rgba(20, 83, 45, 0.92)';
        } else {
            header.style.backdropFilter = 'none';
            header.style.background = 'linear-gradient(135deg, #14532d, #166534)';
        }
    };
    window.addEventListener('scroll', onScroll);
    onScroll();
}

// 🛒 Cart Logic
function addToCart(productId) {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        showToast("Please login first!", "error");
        setTimeout(() => window.location.href = "login.html", 1500);
        return;
    }

    fetch(`${API_BASE}/cart/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, product_id: productId, quantity: 1 })
    })
    .then(res => res.json())
    .then(data => {
        showToast("Added to Cart!", "success");
        updateCartBadge();
        animateCartBadge();
    });
}

function animateCartBadge() {
    const badges = document.querySelectorAll('.cart-badge');
    badges.forEach(badge => {
        badge.classList.remove('cart-badge-bounce');
        // Force reflow so repeated adds still animate.
        void badge.offsetWidth;
        badge.classList.add('cart-badge-bounce');
    });
}

function updateCartBadge() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    fetch(`${API_BASE}/cart/${user.id}`)
    .then(res => res.json())
    .then(data => {
        const count = data.items ? data.items.length : 0;
        document.querySelectorAll('#cart-badge, #mobile-cart-badge').forEach(badge => {
            badge.innerText = count;
        });
    });
}

function removeFromCart(productId) {
    const user = JSON.parse(localStorage.getItem("user"));
    fetch(`${API_BASE}/cart/remove`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, product_id: productId })
    }).then(() => renderCartPage());
}

function updateCartQty(productId, qty) {
    const user = JSON.parse(localStorage.getItem("user"));
    fetch(`${API_BASE}/cart/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, product_id: productId, quantity: parseInt(qty) })
    }).then(() => renderCartPage());
}

// 🤝 Negotiation Logic
function openNegotiationModal(productId, productName, originalPrice) {
    const modal = document.getElementById('negotiate-modal');
    if (!modal) return;
    document.getElementById('neg-product-id').value = productId;
    document.getElementById('neg-product-name').innerText = productName;
    document.getElementById('neg-original-price').innerText = `₹${originalPrice}`;
    modal.style.display = 'flex';
}

function submitNegotiation(e) {
    if (e) e.preventDefault();
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        showToast("Please login, then negotiate!", "error");
        return;
    }

    const productId = document.getElementById('neg-product-id').value;
    const negotiated_price = document.getElementById('neg-price').value;
    const message = document.getElementById('neg-message').value;

    fetch(`${API_BASE}/negotiate/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, user_name: user.name, product_id: productId, negotiated_price, message })
    })
    .then(res => res.json())
    .then(data => {
        showToast("Negotiation offer sent successfully!", "success");
        document.getElementById('negotiate-modal').style.display = 'none';
    });
}

function renderNegotiationsPage() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    fetch(`${API_BASE}/negotiate/${user.id}`)
    .then(res => res.json())
    .then(list => {
        const grid = document.getElementById('negotiations-grid');
        if (!grid) return;

        grid.innerHTML = "";
        if (list.length === 0) {
            grid.innerHTML = "<h3>You haven't made any negotiation offers yet.</h3>";
            return;
        }

        list.forEach(neg => {
            const card = document.createElement('div');
            card.className = "cart-item";
            card.style.flexDirection = "column";
            const negotiationCategory = inferProductCategory({ name: neg.product_name, category: neg.category }) || "farm";
            const negotiationProduct = {
                name: neg.product_name,
                category: neg.category || negotiationCategory,
                image_url: neg.image_url || neg.product_image || "",
                suggested_image_url: neg.suggested_image_url || "",
            };
            const negotiationImage = resolveImageUrl(negotiationProduct);
            const negotiationAlt = buildProductAltText(negotiationProduct, neg.product_name || "farm produce");
            
            let statusColor = "#6B7280";
            const currentStatus = (neg.status || '').toLowerCase().trim();
            
            if(currentStatus === "accepted") statusColor = "#2D6A4F";
            if(currentStatus === "rejected") statusColor = "#E25C5C";
            if(currentStatus === "counter_offered" || currentStatus === "countered") statusColor = "#D97706";

            let counterSection = '';
            if (currentStatus === "counter_offered" || currentStatus === "countered") {
                counterSection = `
                    <div style="margin-top:1.5rem; padding-top:1.5rem; border-top:1px dashed var(--border)">
                        <h4 style="color:var(--primary); margin-bottom:0.5rem">Farmer's Counter Offer</h4>
                        <div style="background:#FFFBEB; padding:10px; border-radius:8px; border:1px solid #FEF3C7; font-size:14px; margin-bottom:1rem;">
                            "${neg.counter_message || 'I would prefer a slightly different price.'}"
                        </div>
                        <div style="display:flex; gap:10px; align-items:center">
                            <input type="number" id="re-neg-price-${neg._id}" placeholder="New Price" class="input-field" style="width:120px; flex:none" />
                            <input type="text" id="re-neg-msg-${neg._id}" placeholder="Your reply..." class="input-field" />
                            <button class="btn-auth" style="padding:0.8rem 1.5rem; width:auto; border-radius:8px" onclick="updateNegotiation('${neg._id}')">Reply</button>
                            <button style="background:#FFEAEA; color:#E25C5C; border:none; border-radius:8px; padding:0.8rem 1.5rem; cursor:pointer; font-weight:700" onclick="rejectNegotiation('${neg._id}')">Reject</button>
                        </div>
                    </div>
                `;
            } else if (currentStatus === 'accepted') {
                counterSection = `
                     <div style="margin-top:1.5rem; padding-top:1.5rem; border-top:1px dashed var(--border); display:flex; gap:10px; align-items:center">
                        <label style="font-size:12px; font-weight:700; color:var(--neutral-mid)">Qty (kg):</label>
                        <input type="number" id="accept-qty-${neg._id}" value="1" min="1" class="input-field" style="width:80px; padding:0.5rem" />
                        <button class="btn-auth" style="padding:0.7rem 1.5rem; width:auto; border-radius:8px" onclick="addNegotiatedToCart('${neg.product_id}', '${neg.negotiated_price}', '${neg._id}')">Add to Cart at ₹${neg.negotiated_price}</button>
                     </div>
                `;
            }

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:1rem; margin-bottom:1rem">
                    <div style="display:flex; align-items:center; gap:0.8rem">
                        <img
                            src="${negotiationImage}"
                            class="negotiation-product-image img-skeleton"
                            loading="lazy"
                            alt="${escapeHtml(negotiationAlt)}"
                            data-crop-name="${escapeHtml(neg.product_name || '')}"
                            data-category="${escapeHtml(negotiationCategory)}"
                            onload="handleImageLoad(this)"
                            onerror="handleProductImageError(this)"
                        >
                        <h3 class="product-name" style="margin-bottom:0">${neg.product_name}</h3>
                    </div>
                    <div class="product-badge" style="position:static; background:${statusColor}22; color:${statusColor}">${neg.status.toUpperCase()}</div>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem; margin-bottom:1.5rem">
                    <div>
                        <div style="font-size:12px; color:var(--neutral-mid)">Original Price</div>
                        <div style="font-weight:700">₹${neg.original_price}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:var(--neutral-mid)">Negotiated Price</div>
                        <div style="font-weight:700; color:var(--primary)">₹${neg.negotiated_price}</div>
                    </div>
                </div>
                <div>
                    <div style="font-size:12px; color:var(--neutral-mid); margin-bottom:5px">Your Last Message</div>
                    <div style="background:#f9fafb; padding:10px; border-radius:8px; font-size:14px; border:1px solid var(--border)">
                        "${neg.message}"
                    </div>
                </div>
                ${counterSection}
            `;
            grid.appendChild(card);
        });
    });
}

function updateNegotiation(negId) {
    const user = JSON.parse(localStorage.getItem("user"));
    const price = document.getElementById(`re-neg-price-${negId}`).value;
    const msg = document.getElementById(`re-neg-msg-${negId}`).value;

    if (!price || !msg) {
        showToast("Please enter a new price and message.", "error");
        return;
    }

    fetch(`${API_BASE}/negotiate/update/${negId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ negotiated_price: price, message: msg })
    }).then(res => res.json()).then(data => {
        showToast("Counter offer sent back to farmer!", "success");
        setTimeout(() => window.location.reload(), 1000);
    });
}

function rejectNegotiation(negId) {
    if(!confirm("Are you sure you want to reject the farmer's offer?")) return;
    fetch(`${API_BASE}/negotiate/reject/${negId}`, {
        method: "POST"
    }).then(res => res.json()).then(data => {
        showToast("Offer rejected securely.", "neutral");
        setTimeout(() => window.location.reload(), 1000);
    });
}

function addNegotiatedToCart(productId, negotiatedPrice, negId) {
    const user = JSON.parse(localStorage.getItem("user"));
    const qty = document.getElementById(`accept-qty-${negId}`).value;
    
    fetch(`${API_BASE}/cart/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            user_id: user.id, 
            product_id: productId, 
            quantity: parseInt(qty),
            negotiated_price: negotiatedPrice,
            neg_id: negId
        })
    }).then(res => res.json()).then(data => {
        showToast("Added negotiated product to cart!", "success");
        updateCartBadge();
        animateCartBadge();
    });
}

// 💖 Wishlist Logic
let userWishlist = [];

function fetchWishlist() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return Promise.resolve([]);
    
    return fetch(`${API_BASE}/wishlist/${user.id}`)
    .then(res => res.json())
    .then(data => {
        userWishlist = data.items.map(item => item._id);
        return userWishlist;
    });
}

function toggleWishlist(productId, btnElement) {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
        showToast("Please login, then save favorites!", "error");
        return;
    }

    fetch(`${API_BASE}/wishlist/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, product_id: productId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "added") {
            btnElement.classList.add('active');
            userWishlist.push(productId);
            showToast("Added to Wishlist!", "success");
        } else {
            btnElement.classList.remove('active');
            userWishlist = userWishlist.filter(id => id !== productId);
            showToast("Removed from Wishlist", "neutral");
        }
        // If we are on wishlist page, re-render
        if (window.location.pathname.includes('wishlist.html')) renderWishlistPage();
    });
}

function renderWishlistPage() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    fetch(`${API_BASE}/wishlist/${user.id}`)
    .then(res => res.json())
    .then(data => {
        const grid = document.getElementById('wishlist-grid');
        if (!grid) return;

        grid.innerHTML = "";
        if (data.items.length === 0) {
            grid.innerHTML = `
                <div class="wishlist-empty" style="grid-column: 1/-1">
                    <div style="font-size: 4rem; margin-bottom: 1rem">💝</div>
                    <h2 class="display-font">Your wishlist is empty</h2>
                    <p style="color:var(--neutral-mid); margin-bottom: 2rem">Save your favorite organic produce to find them later.</p>
                    <a href="index.html" class="btn-add" style="text-decoration:none">Go to Marketplace</a>
                </div>
            `;
            return;
        }

        data.items.forEach(p => {
            const card = document.createElement("div");
            card.className = "product-card";
            const category = inferProductCategory(p) || 'farm';
            const imageUrl = resolveImageUrl(p);
            const cropLabel = p.crop_name || p.name || '';
            const imageAlt = buildProductAltText(p, cropLabel);
            
            card.innerHTML = `
                <button class="wishlist-btn active" onclick="toggleWishlist('${p._id}', this)">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </button>
                <img
                    src="${imageUrl}"
                    class="product-image wishlist-product-image img-skeleton"
                    loading="lazy"
                    alt="${escapeHtml(imageAlt)}"
                    data-crop-name="${escapeHtml(cropLabel)}"
                    data-category="${escapeHtml(category)}"
                    onclick="window.location.href='product.html?id=${p._id}'"
                    onload="handleImageLoad(this)"
                    onerror="handleProductImageError(this)"
                >
                <div class="product-info">
                    <div class="farmer-tag">🧑‍🌾 ${p.farmer.name}</div>
                    <h3 class="product-name">${p.name}</h3>
                    <div class="product-footer">
                        <span class="price">₹${p.price}</span>
                        <button class="btn-add" onclick="addToCart('${p._id}')">Add to Cart</button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    });
}

// 🛍️ Product Logic
let allProducts = [];

function normalizeCategoryValue(value) {
    const raw = String(value || '').trim().toLowerCase();
    const aliases = {
        vegetables: 'vegetable',
        vegetable: 'vegetable',
        fruits: 'fruit',
        fruit: 'fruit',
        grains: 'grain',
        grain: 'grain',
        dairy: 'dairy',
        honey: 'honey',
        all: 'all'
    };
    return aliases[raw] || raw;
}

function inferProductCategory(product) {
    const explicit = normalizeCategoryValue(product?.category || '');
    if (explicit && explicit !== 'all') return explicit;

    const text = [product?.crop_name, product?.name, product?.description]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

    if (!text) return '';
    if (/(honey|madhu)/.test(text)) return 'honey';
    if (/(milk|dairy|paneer|curd|ghee|butter|cheese|yogurt)/.test(text)) return 'dairy';
    if (/(mango|banana|apple|orange|grape|papaya|guava|fruit)/.test(text)) return 'fruit';
    if (/(wheat|rice|maize|grain|millet|barley|bajra|jowar)/.test(text)) return 'grain';
    if (/(lentil|dal|chickpea|chana|moong|urad|rajma|pulse|soybean)/.test(text)) return 'pulse';
    if (/(turmeric|chilli|chili|coriander|cumin|pepper|cardamom|mustard|fenugreek|spice)/.test(text)) return 'spice';
    if (/(cotton|sugarcane|groundnut|sunflower|jute|cash crop)/.test(text)) return 'cash_crop';
    if (/(tomato|onion|potato|brinjal|eggplant|cabbage|carrot|cauliflower|peas|vegetable)/.test(text)) return 'vegetable';
    return '';
}

function localFallbackImage(category) {
    if (typeof getCategoryFallbackImage === "function") {
        return getCategoryFallbackImage(category);
    }

    const normalized = normalizeCategoryValue(category || '');
    const fallbackMap = {
        vegetable: "/buyer/images/placeholders/vegetables-default.jpg",
        fruit: "/buyer/images/placeholders/fruits-default.jpg",
        grain: "/buyer/images/placeholders/grains-default.jpg",
        pulse: "/buyer/images/placeholders/pulses-default.jpg",
        spice: "/buyer/images/placeholders/spices-default.jpg",
        dairy: "/buyer/images/placeholders/farm-default.jpg",
        honey: "/buyer/images/placeholders/farm-default.jpg",
        farm: "/buyer/images/placeholders/farm-default.jpg",
    };
    return fallbackMap[normalized] || fallbackMap.farm;
}

function resolveImageUrl(product) {
    const raw = String(product?.image_url || '').trim();
    if (raw) {
        if (raw.startsWith('uploads/')) return `/farmer/static/${raw}`;
        if (raw.startsWith('/uploads/')) return `/farmer/static/${raw.slice(1)}`;
        if (raw.startsWith('/farmer/static/')) return raw;
        if (raw.startsWith('http://') || raw.startsWith('https://')) return raw;
        if (raw.startsWith('/')) return raw;
        if (raw.startsWith('images/')) return `/${raw}`;
        return `/${raw.replace(/^\/+/, '')}`;
    }

    const suggested = String(product?.suggested_image_url || '').trim();
    if (suggested) return suggested;

    if (typeof getCropImage === "function") {
        return getCropImage(product?.crop_name || product?.name || "", product?.category);
    }
    return localFallbackImage(inferProductCategory(product));
}

function buildProductAltText(product, fallback = "farm produce") {
    const cropName = String(product?.crop_name || product?.name || fallback || "farm produce").trim();
    const farmerLocation = String(
        product?.farmer?.location || product?.location || product?.farmer_location?.state || ""
    ).trim();
    if (farmerLocation) return `Fresh ${cropName} from ${farmerLocation}`;
    return `Fresh ${cropName} from Krishi Connect`;
}

function handleImageLoad(imgElement) {
    if (!imgElement) return;
    imgElement.classList.remove("img-skeleton");
}

function handleProductImageError(imgElement) {
    if (!imgElement) return;

    const category = imgElement.dataset.category || "farm";
    const step = Number(imgElement.dataset.fallbackStep || "0");

    if (step === 0) {
        imgElement.dataset.fallbackStep = "1";
        const categoryUrl = typeof getCropImage === "function"
            ? getCropImage("", category)
            : localFallbackImage(category);
        if (categoryUrl && categoryUrl !== imgElement.src) {
            imgElement.src = categoryUrl;
            return;
        }
    }

    if (step <= 1) {
        imgElement.dataset.fallbackStep = "2";
        const localCategory = localFallbackImage(category);
        if (localCategory && localCategory !== imgElement.src) {
            imgElement.src = localCategory;
            return;
        }
    }

    imgElement.onerror = null;
    imgElement.src = localFallbackImage("farm");
}

function setImageFallback(imgElement, category) {
    if (!imgElement) return;
    imgElement.dataset.category = category || imgElement.dataset.category || "farm";
    imgElement.dataset.fallbackStep = "1";
    imgElement.onerror = () => {
        imgElement.onerror = null;
        imgElement.src = localFallbackImage("farm");
    };
    imgElement.src = localFallbackImage(category || "farm");
}

function initMarketplace() {
    const grid = document.getElementById('product-grid');
    if (!grid) return;

    fetchWishlist().then(() => {
        fetch(`${API_BASE}/products`)
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to load products (${res.status})`);
            }
            return res.json();
        })
        .then(products => {
            allProducts = Array.isArray(products) ? products : [];
            applyFilters();
        })
        .catch(() => {
            allProducts = [];
            renderProducts([]);
            showToast("Unable to load products. Please check DB connection.", "error");
        });
    });
}

function applyFilters() {
    const grid = document.getElementById('product-grid');
    if (!grid) return;

    const category = normalizeCategoryValue(document.getElementById('filter-category')?.value || 'all');
    const location = document.getElementById('filter-location')?.value || 'all';
    const minPrice = parseFloat(document.getElementById('filter-min-price')?.value) || 0;
    const maxPrice = parseFloat(document.getElementById('filter-max-price')?.value) || Infinity;
    const minQty = parseInt(document.getElementById('filter-quantity')?.value) || 0;
    const sort = document.getElementById('filter-sort')?.value || 'default';
    const search = document.getElementById('search-input')?.value.toLowerCase() || '';

    let filtered = allProducts.filter(p => {
        const name = String(p.name || '').toLowerCase();
        const cropName = String(p.crop_name || '').toLowerCase();
        const description = String(p.description || '').toLowerCase();
        const rawCategory = String(p.category || '');
        const productCategory = inferProductCategory(p);

        if (
            search &&
            !name.includes(search) &&
            !cropName.includes(search) &&
            !description.includes(search) &&
            !rawCategory.toLowerCase().includes(search)
        ) return false;
        if (category !== 'all' && productCategory !== category) return false;
        if (location !== 'all' && !p.farmer.location.toLowerCase().includes(location.toLowerCase())) return false;
        if (p.price < minPrice || p.price > maxPrice) return false;
        const qty = p.quantity || p.stock || 100;
        if (qty < minQty) return false;
        return true;
    });

    if (sort === 'price-low') {
        filtered.sort((a, b) => a.price - b.price);
    } else if (sort === 'price-high') {
        filtered.sort((a, b) => b.price - a.price);
    } else if (sort === 'rating') {
        filtered.sort((a, b) => b.farmer.rating - a.farmer.rating);
    }

    renderProducts(filtered);
}

function resetFilters() {
    document.getElementById('filter-category').value = 'all';
    document.getElementById('filter-location').value = 'all';
    document.getElementById('filter-min-price').value = '';
    document.getElementById('filter-max-price').value = '';
    document.getElementById('filter-quantity').value = '';
    document.getElementById('filter-sort').value = 'default';
    document.getElementById('search-input').value = '';
    applyFilters();
}

function renderProducts(products) {
    const grid = document.getElementById('product-grid');
    const countEl = document.getElementById('product-count');
    if (countEl) countEl.innerText = `Showing ${products.length} fresh products`;
    grid.innerHTML = "";
    
    if (products.length === 0) {
        grid.innerHTML = "<div style='grid-column:1/-1; text-align:center; padding:4rem; color:var(--neutral-mid);'><div style='font-size:3rem; margin-bottom:1rem;'>🚜</div><h3 class='display-font' style='font-size:1.5rem'>No crop matches your filters</h3><p>Try adjusting your search criteria</p></div>";
        return;
    }

    products.forEach(p => {
        const card = document.createElement("div");
        card.className = "product-card";
        const safeName = p.name.replace(/'/g, "\\'");
        const isWishlisted = userWishlist.includes(p._id);
        const category = inferProductCategory(p) || 'farm';
        const imageUrl = resolveImageUrl(p);
        const cropLabel = p.crop_name || p.name || '';
        const imageAlt = buildProductAltText(p, cropLabel);
        
        card.innerHTML = `
            <button class="wishlist-btn ${isWishlisted ? 'active' : ''}" onclick="toggleWishlist('${p._id}', this)">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </button>
            <img
                src="${imageUrl}"
                class="product-image img-skeleton"
                loading="lazy"
                alt="${escapeHtml(imageAlt)}"
                data-crop-name="${escapeHtml(cropLabel)}"
                data-category="${escapeHtml(category)}"
                onclick="window.location.href='product.html?id=${p._id}'"
                onload="handleImageLoad(this)"
                onerror="handleProductImageError(this)"
            >
            ${p.isOrganic ? '<span class="product-badge badge-organic">Organic</span>' : ''}
            ${p.isFresh ? '<span class="product-badge badge-fresh" style="top:35px">Fresh Today</span>' : ''}
            <div class="product-info">
                <div class="farmer-tag">🧑‍🌾 ${p.farmer.name} • ${p.farmer.location}</div>
                <h3 class="product-name">${p.name}</h3>
                <div class="product-rating">⭐⭐⭐⭐ ${p.farmer.rating}</div>
                <div class="product-footer" style="flex-wrap:wrap; gap:10px">
                    <span class="price">₹${p.price}</span>
                    <div style="display:flex; gap:5px; width:100%">
                        <button class="btn-add" style="flex:1" onclick="addToCart('${p._id}')">Add to Cart</button>
                        <button class="filter-chip" style="flex:1; border-color:var(--primary); color:var(--primary)" 
                                onclick="openNegotiationModal('${p._id}', '${safeName}', ${p.price})">Negotiate</button>
                    </div>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderProductDetail() {
    const urlParams = new URL(window.location.href).searchParams;
    const pid = urlParams.get('id');
    if (!pid) return;

    fetchWishlist().then(() => {
        fetch(`${API_BASE}/products/${pid}`)
        .then(res => res.json())
        .then(p => {
            const isWishlisted = userWishlist.includes(p._id);
            const detailContainer = document.querySelector('.product-detail-layout');
            if (detailContainer) {
                // Add heart button to detail page if it doesn't exist
                if (!document.getElementById('detail-wishlist-btn')) {
                    const btn = document.createElement('button');
                    btn.id = 'detail-wishlist-btn';
                    btn.className = `wishlist-btn ${isWishlisted ? 'active' : ''}`;
                    btn.style.top = '20px';
                    btn.style.right = '20px';
                    btn.style.width = '45px';
                    btn.style.height = '45px';
                    btn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`;
                    btn.onclick = () => toggleWishlist(p._id, btn);
                    detailContainer.style.position = 'relative';
                    detailContainer.appendChild(btn);
                }
            }

            const detailCategory = inferProductCategory(p) || 'farm';
            const detailImage = document.getElementById('p-image');
            detailImage.classList.add("img-skeleton");
            detailImage.dataset.category = detailCategory;
            detailImage.dataset.cropName = p.crop_name || p.name || "";
            detailImage.dataset.fallbackStep = "0";
            detailImage.alt = buildProductAltText(p, p.crop_name || p.name || "farm produce");
            detailImage.onload = () => handleImageLoad(detailImage);
            detailImage.src = resolveImageUrl(p);
            detailImage.onerror = () => handleProductImageError(detailImage);
            document.getElementById('p-name').innerText = p.name;
            document.getElementById('p-desc').innerText = p.description || 'Premium farm produce freshly curated for you.';
            document.getElementById('p-price').innerHTML = `₹${p.price}<span style="font-size:1.2rem; color:var(--neutral-mid); font-family: 'DM Sans', sans-serif;">/kg</span>`;
            
            const qty = p.quantity || p.stock || 100;
            document.getElementById('p-qty').innerText = `${qty} kg available`;

            // Farmer Profile Injection
            document.getElementById('p-farmer-name').innerText = p.farmer.name;
            document.getElementById('p-farmer-initial').innerText = p.farmer.name.charAt(0).toUpperCase();
            document.getElementById('p-farmer-location').innerText = `📍 ${p.farmer.location}`;
            document.getElementById('p-farmer-rating').innerText = `⭐⭐⭐⭐ ${p.farmer.rating || '4.5'}`;
            
            // Category & Badges
            document.getElementById('p-category').innerText = p.category || 'Farm Produce';
            let badgesHtml = '';
            if (p.isOrganic) badgesHtml += '<span class="product-badge badge-organic" style="position:static; font-size: 0.8rem; padding: 6px 14px;">Organic</span>';
            if (p.isFresh) badgesHtml += '<span class="product-badge badge-fresh" style="position:static; font-size: 0.8rem; padding: 6px 14px;">Fresh Today</span>';
            document.getElementById('p-badges').innerHTML = badgesHtml;

            document.getElementById('buy-btn').onclick = () => addToCart(p._id);
            
            const negBtn = document.getElementById('neg-btn');
            if (negBtn) {
                const safeName = p.name.replace(/'/g, "\\'");
                negBtn.onclick = () => openNegotiationModal(p._id, safeName, p.price);
            }
        });
    });
}

function renderCartPage() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    fetch(`${API_BASE}/cart/${user.id}`)
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('cart-list');
        const summary = document.getElementById('cart-summary-box');
        
        let total = 0;
        if (data.items) {
            data.items.forEach(item => {
                total += (parseFloat(item.price) * parseInt(item.quantity));
            });
        }

        // Update total across ALL relevant elements
        const totalElements = document.querySelectorAll('#order-total');
        totalElements.forEach(el => el.innerText = `₹${total}`);

        // Inject total into UPI modal if it exists
        const upiTotal = document.getElementById('upi-amount');
        if (upiTotal) upiTotal.innerText = `₹${total}`;

        if (container) {
            container.innerHTML = "";
            if (!data.items || data.items.length === 0) {
                container.innerHTML = "<div style='grid-column:1/-1; text-align:center; padding:3rem'><h3>🌾 Your cart is currently empty</h3><br><a href='index.html' class='btn-add' style='text-decoration:none'>Discover Fresh Produce</a></div>";
                if (summary) summary.style.display = "none";
                return;
            } else {
                if (summary) summary.style.display = "block";
            }

            data.items.forEach(item => {
                const card = document.createElement("div");
                card.className = "cart-item";
                const itemCategory = inferProductCategory(item) || "farm";
                const itemProduct = {
                    name: item.name,
                    category: itemCategory,
                    image_url: item.image,
                };
                const itemImage = resolveImageUrl(itemProduct);
                const itemAlt = buildProductAltText(itemProduct, item.name || "farm produce");
                card.innerHTML = `
                    <img
                        src="${itemImage}"
                        class="cart-img img-skeleton"
                        loading="lazy"
                        alt="${escapeHtml(itemAlt)}"
                        data-crop-name="${escapeHtml(item.name || '')}"
                        data-category="${escapeHtml(itemCategory)}"
                        onload="handleImageLoad(this)"
                        onerror="handleProductImageError(this)"
                    >
                    <div style="flex:1">
                        <h3 class="product-name" style="margin-bottom:5px">${item.name}</h3>
                        <p style="color:var(--primary); font-weight:700; font-size:1.1rem">₹${item.price} per kg</p>
                        <div style="margin-top:15px; display:flex; gap:12px; align-items:center">
                            <span style="font-size:14px; color:var(--neutral-mid)">Qty:</span>
                            <div style="display:flex; align-items:center; border:1px solid var(--border); border-radius:6px; overflow:hidden">
                                <button onclick="updateCartQty('${item.product_id}', ${parseInt(item.quantity) - 1})" style="padding:5px 10px; border:none; background:#f3f4f6; cursor:pointer">-</button>
                                <span style="padding:0 15px; font-weight:700">${item.quantity}</span>
                                <button onclick="updateCartQty('${item.product_id}', ${parseInt(item.quantity) + 1})" style="padding:5px 10px; border:none; background:#f3f4f6; cursor:pointer">+</button>
                            </div>
                        </div>
                    </div>
                    <button class="filter-chip" style="background:#FFEAEA; color:#E25C5C; border:none; height:fit-content" 
                            onclick="removeFromCart('${item.product_id}')">Remove</button>
                `;
                container.appendChild(card);
            });
        }
    });
}

function handlePlaceOrder(e) {
    if (e) e.preventDefault();
    const address = document.getElementById('address').value;
    if (!address) {
        showToast("Please enter a delivery address", "error");
        return;
    }
    
    const paymentMethod = document.querySelector('input[name="payment"]:checked').value;

    if (paymentMethod === "UPI") {
        const modal = document.getElementById('upi-modal');
        if (modal) modal.style.display = 'flex';
    } else {
        finalizeOrder();
    }
}

function finalizeOrder() {
    const user = JSON.parse(localStorage.getItem("user"));
    const address = document.getElementById('address').value;
    const payment = document.querySelector('input[name="payment"]:checked').value;

    fetch(`${API_BASE}/orders/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, address, payment_method: payment })
    })
    .then(res => res.json())
    .then(data => {
        const modal = document.getElementById('upi-modal');
        if (modal) modal.style.display = 'none';
        showToast("Success! Order placed.", "success");
        setTimeout(() => window.location.href = "orders.html", 1000);
    });
}

function renderOrdersPage() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    fetch(`${API_BASE}/orders/${user.id}`)
    .then(res => res.json())
    .then(orders => {
        const grid = document.getElementById('orders-grid');
        if (!grid) return;

        grid.innerHTML = "";
        if (orders.length === 0) {
            grid.innerHTML = "<h3>You haven't placed any orders yet.</h3>";
            return;
        }

        orders.forEach(order => {
            const card = document.createElement('div');
            card.className = "cart-item";
            card.style.flexDirection = "column";
            const itemRows = (order.items || []).map(item => {
                const itemCategory = inferProductCategory(item) || 'farm';
                const itemProduct = {
                    name: item.name,
                    category: itemCategory,
                    image_url: item.image,
                };
                const itemImage = resolveImageUrl(itemProduct);
                const itemAlt = buildProductAltText(itemProduct, item.name || "farm produce");
                return `
                    <div class="order-item-row">
                        <div class="order-item-left">
                            <img
                                src="${itemImage}"
                                class="order-item-image img-skeleton"
                                loading="lazy"
                                alt="${escapeHtml(itemAlt)}"
                                data-crop-name="${escapeHtml(item.name || '')}"
                                data-category="${escapeHtml(itemCategory)}"
                                onload="handleImageLoad(this)"
                                onerror="handleProductImageError(this)"
                            >
                            <span>${item.name} x ${item.quantity}</span>
                        </div>
                        <span>₹${item.price * item.quantity}</span>
                    </div>
                `;
            }).join('');

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:1rem; margin-bottom:1rem">
                    <div>
                        <span style="font-weight:700">Order ID: #${order._id.slice(-6).toUpperCase()}</span>
                        <div style="color:var(--neutral-mid); font-size:12px">${new Date(order.created_at).toLocaleString()}</div>
                    </div>
                    <div class="product-badge badge-organic" style="position:static">${order.status.toUpperCase()}</div>
                </div>
                <div>
                    ${itemRows}
                </div>
                <div style="margin-top:1rem; border-top:1px solid var(--border); padding-top:1rem; display:flex; justify-content:space-between; font-weight:700">
                    <span>Total Paid (${order.payment_method})</span>
                    <span style="color:var(--primary)">₹${order.total_price}</span>
                </div>
            `;
            grid.appendChild(card);
        });
    });
}

// 🍞 Toast System
function showToast(msg, type = "success") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderLeftColor = type === 'success' ? '#52B788' : '#E25C5C';
    toast.innerHTML = `<span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// 🚗 Initial State Checks
document.addEventListener('DOMContentLoaded', () => {
    initBuyerNavbar();
    updateCartBadge();
});
// 🗺️ Map Discovery Logic
function initMapView() {
    const mapElement = document.getElementById('map');
    if (!mapElement || typeof L === 'undefined') return;

    const sidebar = document.getElementById('map-sidebar');
    const sidebarToggle = document.getElementById('map-sidebar-toggle');
    const mapShell = document.querySelector('.map-shell');
    const sidebarList = document.getElementById('map-sidebar-list');
    const sidebarCount = document.getElementById('map-sidebar-count');
    const categorySelect = document.getElementById('map-filter-category');
    const priceMinInput = document.getElementById('map-price-min');
    const priceMaxInput = document.getElementById('map-price-max');
    const priceMinLabel = document.getElementById('map-price-min-label');
    const priceMaxLabel = document.getElementById('map-price-max-label');
    const nearMeBtn = document.getElementById('map-near-me-btn');
    const recenterBtn = document.getElementById('map-recenter-btn');
    const resetFiltersBtn = document.getElementById('map-reset-filters-btn');
    const loadingOverlay = document.getElementById('map-loading');

    const defaultCenter = [22.3094, 72.1362];
    const defaultZoom = 7;

    const map = L.map('map', { zoomControl: true }).setView(defaultCenter, defaultZoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const mapState = {
        entries: [],
        visibleEntries: [],
        userCoords: null,
        sidebarDesktopCollapsed: false,
        sidebarMobileOpen: false
    };

    const categoryMeta = {
        vegetable: { emoji: '🥬', label: 'Vegetables' },
        fruit: { emoji: '🍊', label: 'Fruits' },
        grain: { emoji: '🌾', label: 'Grains' },
        other: { emoji: '🌿', label: 'Other Crops' }
    };

    const markerLayer = typeof L.markerClusterGroup === 'function'
        ? L.markerClusterGroup({
            showCoverageOnHover: false,
            spiderfyOnMaxZoom: true,
            disableClusteringAtZoom: 12,
            iconCreateFunction(cluster) {
                return L.divIcon({
                    html: `<div class="kc-cluster">${cluster.getChildCount()}</div>`,
                    className: '',
                    iconSize: [42, 42]
                });
            }
        })
        : L.layerGroup();

    markerLayer.addTo(map);

    const geoMap = {
        ahmedabad: [23.0225, 72.5714],
        anand: [22.5645, 72.9289],
        mehsana: [23.5880, 72.3693],
        rajkot: [22.3039, 70.8022],
        vadodara: [22.3072, 73.1812],
        surat: [21.1702, 72.8311],
        bhavnagar: [21.7645, 72.1519],
        amreli: [21.6032, 71.2221],
        junagadh: [21.5222, 70.4579],
        mumbai: [19.0760, 72.8777],
        pune: [18.5204, 73.8567],
        jaipur: [26.9124, 75.7873],
        patna: [25.5941, 85.1376],
        ludhiana: [30.9010, 75.8573],
        vellore: [12.9165, 79.1325],
        delhi: [28.6139, 77.2090],
        indore: [22.7196, 75.8577],
        bengaluru: [12.9716, 77.5946],
        hyderabad: [17.3850, 78.4867],
        gujarat: [22.2587, 71.1924],
        maharashtra: [19.7515, 75.7139],
        rajasthan: [27.0238, 74.2179],
        bihar: [25.0961, 85.3131],
        punjab: [31.1471, 75.3412],
        tamilnadu: [11.1271, 78.6569],
        karnataka: [15.3173, 75.7139],
        telangana: [18.1124, 79.0193],
        madhyapradesh: [22.9734, 78.6569],
        uttarpradesh: [26.8467, 80.9462],
        haryana: [29.0588, 76.0856]
    };

    const locationAliases = {
        ahemdabad: 'ahmedabad',
        'ahmedabad city': 'ahmedabad',
        'new ahmedabad': 'ahmedabad',
        'mumbai city': 'mumbai',
        'pune city': 'pune',
        'tamil nadu': 'tamilnadu',
        'madhya pradesh': 'madhyapradesh',
        'uttar pradesh': 'uttarpradesh'
    };

    const inlandFallbackKeys = [
        'ahmedabad',
        'anand',
        'mehsana',
        'rajkot',
        'vadodara',
        'jaipur',
        'patna',
        'ludhiana',
        'vellore',
        'indore'
    ];

    function setLoading(isLoading) {
        if (loadingOverlay) loadingOverlay.classList.toggle('show', !!isLoading);
    }

    function stableHash(value) {
        const text = String(value || '');
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            hash = ((hash << 5) - hash) + text.charCodeAt(i);
            hash |= 0;
        }
        return Math.abs(hash);
    }

    function asFloat(value) {
        const parsed = parseFloat(value);
        return Number.isFinite(parsed) ? parsed : null;
    }

    function isPlausibleIndiaCoords(lat, lng) {
        return lat >= 6 && lat <= 38 && lng >= 67 && lng <= 98;
    }

    function extractExplicitCoords(product) {
        const candidates = [];
        const coords = product?.coordinates;
        if (Array.isArray(coords) && coords.length >= 2) {
            candidates.push([coords[0], coords[1]]);
            candidates.push([coords[1], coords[0]]);
        }

        candidates.push([product?.latitude, product?.longitude]);
        candidates.push([product?.lat, product?.lng]);
        candidates.push([product?.lat, product?.lon]);
        candidates.push([product?.location?.lat, product?.location?.lng]);
        candidates.push([product?.location?.latitude, product?.location?.longitude]);
        candidates.push([product?.farmer_location?.lat, product?.farmer_location?.lng]);
        candidates.push([product?.farmer_location?.latitude, product?.farmer_location?.longitude]);

        for (const pair of candidates) {
            const lat = asFloat(pair[0]);
            const lng = asFloat(pair[1]);
            if (lat === null || lng === null) continue;
            if (Math.abs(lat) > 90 || Math.abs(lng) > 180) continue;
            if (!isPlausibleIndiaCoords(lat, lng)) continue;
            return [lat, lng];
        }
        return null;
    }

    function jitterCoords(baseCoords, seed) {
        const h = stableHash(seed);
        const latOffset = (((h % 1000) / 1000) - 0.5) * 0.08;
        const lngOffset = ((((Math.floor(h / 1000)) % 1000) / 1000) - 0.5) * 0.08;
        return [baseCoords[0] + latOffset, baseCoords[1] + lngOffset];
    }

    function normalizeLocationKey(rawLocation) {
        const cleaned = String(rawLocation || '')
            .trim()
            .toLowerCase()
            .replace(/[^a-z\s]/g, ' ')
            .replace(/\s+/g, ' ');
        if (!cleaned) return '';
        return locationAliases[cleaned] || cleaned;
    }

    function resolveCoords(product, seed) {
        const explicitCoords = extractExplicitCoords(product);
        if (explicitCoords) return explicitCoords;

        const locationText = String(
            product?.farmer?.location || product?.farmer_location?.state || product?.farmer_location || ''
        ).trim();

        const normalized = normalizeLocationKey(locationText);
        if (normalized && geoMap[normalized]) {
            return jitterCoords(geoMap[normalized], seed);
        }

        if (normalized) {
            for (const key of Object.keys(geoMap)) {
                if (normalized.includes(key) || key.includes(normalized)) {
                    return jitterCoords(geoMap[key], seed);
                }
            }
        }

        const fallbackKey = inlandFallbackKeys[stableHash(seed) % inlandFallbackKeys.length];
        return jitterCoords(geoMap[fallbackKey], seed);
    }

    function parsePrice(value) {
        const direct = Number(value);
        if (Number.isFinite(direct)) return direct;
        const cleaned = String(value ?? '').replace(/[^0-9.]/g, '');
        const parsed = parseFloat(cleaned);
        return Number.isFinite(parsed) ? parsed : 0;
    }

    function formatPrice(value) {
        const amount = parsePrice(value);
        if (!Number.isFinite(amount)) return '0';
        return amount.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    }

    function toSafeText(value, fallback = '-') {
        const text = String(value ?? '').trim();
        return text || fallback;
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function getCategoryBucket(product) {
        const normalized = normalizeCategoryValue(inferProductCategory(product) || product?.category || '');
        if (normalized === 'vegetable' || normalized === 'fruit' || normalized === 'grain') return normalized;
        return 'other';
    }

    function createMarkerIcon(bucket) {
        const category = categoryMeta[bucket] ? bucket : 'other';
        const emoji = categoryMeta[category].emoji;
        return L.divIcon({
            className: '',
            html: `
                <div class="kc-marker ${category}">
                    <span class="kc-marker-ping"></span>
                    <span class="kc-marker-core">${emoji}</span>
                </div>
            `,
            iconSize: [34, 34],
            iconAnchor: [17, 30],
            popupAnchor: [0, -24]
        });
    }

    function getQuantity(product) {
        const value = parseFloat(product?.quantity ?? product?.stock_qty ?? product?.stock ?? 0);
        return Number.isFinite(value) && value > 0 ? value : 0;
    }

    function popupMarkup(entry) {
        const product = entry.product;
        const productId = String(product?._id || product?.id || '');
        const productName = escapeHtml(toSafeText(product?.name, 'Fresh Produce'));
        const farmerName = escapeHtml(toSafeText(product?.farmer?.name, 'Verified Farmer'));
        const location = escapeHtml(toSafeText(product?.farmer?.location, 'Gujarat'));
        const qty = entry.quantity > 0 ? `${formatPrice(entry.quantity)} kg` : 'In stock';
        const imageCategory = entry.category === 'other' ? 'farm' : entry.category;
        const detailsHref = productId ? `product.html?id=${encodeURIComponent(productId)}` : 'product.html';
        const imageUrl = resolveImageUrl(product);
        const imageAlt = escapeHtml(buildProductAltText(product, product?.name || "farm produce"));

        return `
            <div class="kc-popup-card">
                <img
                    src="${imageUrl}"
                    class="kc-popup-thumb img-skeleton"
                    loading="lazy"
                    alt="${imageAlt}"
                    data-crop-name="${escapeHtml(product?.crop_name || product?.name || '')}"
                    data-category="${escapeHtml(imageCategory)}"
                    onload="handleImageLoad(this)"
                    onerror="handleProductImageError(this)"
                >
                <div class="kc-popup-body">
                    <div class="kc-popup-category">${categoryMeta[entry.category].label}</div>
                    <h4 class="kc-popup-title">${productName}</h4>
                    <p class="kc-popup-subtitle">🧑‍🌾 ${farmerName} • ${location}</p>
                    <div class="kc-popup-meta">
                        <div class="kc-popup-meta-price">₹${formatPrice(entry.price)}/kg</div>
                        <div class="kc-popup-meta-stock">${qty}</div>
                    </div>
                    <div class="kc-popup-actions">
                        ${
                            productId
                                ? `<button type="button" onclick="addToCart('${escapeHtml(productId)}')" class="kc-popup-btn">Add to Cart</button>`
                                : `<span class="kc-popup-btn" style="opacity:0.6; cursor:not-allowed">Unavailable</span>`
                        }
                        <a href="${detailsHref}" class="kc-popup-link">View Details</a>
                    </div>
                </div>
            </div>
        `;
    }

    function toRadians(deg) {
        return deg * (Math.PI / 180);
    }

    function getDistanceKm(from, to) {
        if (!Array.isArray(from) || !Array.isArray(to)) return null;
        const [lat1, lon1] = from;
        const [lat2, lon2] = to;
        const earthRadius = 6371;
        const dLat = toRadians(lat2 - lat1);
        const dLon = toRadians(lon2 - lon1);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return earthRadius * c;
    }

    function updateSidebar(list) {
        if (!sidebarList) return;
        if (sidebarCount) {
            sidebarCount.innerText = `${list.length} ${list.length === 1 ? 'item' : 'items'}`;
        }

        if (!list.length) {
            sidebarList.innerHTML = `
                <div class="rounded-xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
                    No products match these filters.
                </div>
            `;
            return;
        }

        sidebarList.innerHTML = list.map(entry => {
            const distanceText = entry.distanceKm !== null
                ? `${entry.distanceKm.toFixed(1)} km`
                : 'Enable Near Me';

            return `
                <button type="button" data-map-index="${entry.index}" class="map-product-card">
                    <div class="map-product-top">
                        <div>
                            <p class="map-product-name">${escapeHtml(toSafeText(entry.product.name, 'Fresh Produce'))}</p>
                            <p class="map-product-farmer">${escapeHtml(toSafeText(entry.product.farmer?.name, 'Verified Farmer'))}</p>
                        </div>
                        <span class="map-product-badge ${entry.category}">
                            ${categoryMeta[entry.category].label}
                        </span>
                    </div>
                    <div class="map-product-meta">
                        <span>₹${formatPrice(entry.price)}/kg</span>
                        <span>${distanceText}</span>
                    </div>
                </button>
            `;
        }).join('');

        sidebarList.querySelectorAll('[data-map-index]').forEach(button => {
            button.addEventListener('click', () => {
                const markerIndex = Number(button.getAttribute('data-map-index'));
                const entry = mapState.visibleEntries.find(item => item.index === markerIndex);
                if (!entry) return;
                map.flyTo(entry.coords, 10, { duration: 0.8 });
                entry.marker.openPopup();
                if (window.innerWidth < 768) {
                    mapState.sidebarMobileOpen = false;
                    syncSidebarClasses();
                }
            });
        });
    }

    function fitToEntries(entries) {
        if (!entries.length) {
            map.setView(defaultCenter, defaultZoom);
            return;
        }
        if (entries.length === 1) {
            map.setView(entries[0].coords, 10);
            return;
        }
        const bounds = L.latLngBounds(entries.map(entry => entry.coords));
        if (bounds.isValid()) {
            map.fitBounds(bounds.pad(0.12), { maxZoom: 9 });
        }
    }

    function refreshPriceLabels() {
        if (priceMinLabel) priceMinLabel.innerText = `₹${formatPrice(priceMinInput?.value || 0)}`;
        if (priceMaxLabel) priceMaxLabel.innerText = `₹${formatPrice(priceMaxInput?.value || 0)}`;
    }

    function clampPriceRange(changedInput) {
        if (!priceMinInput || !priceMaxInput) return;
        let minVal = parseFloat(priceMinInput.value) || 0;
        let maxVal = parseFloat(priceMaxInput.value) || 0;
        if (minVal > maxVal) {
            if (changedInput === 'min') {
                maxVal = minVal;
                priceMaxInput.value = String(maxVal);
            } else {
                minVal = maxVal;
                priceMinInput.value = String(minVal);
            }
        }
    }

    function applyMapFilters(options = {}) {
        clampPriceRange();
        refreshPriceLabels();

        const category = normalizeCategoryValue(categorySelect?.value || 'all');
        const minPrice = parseFloat(priceMinInput?.value) || 0;
        const maxPrice = parseFloat(priceMaxInput?.value) || Infinity;

        const filtered = mapState.entries.filter(entry => {
            if (category !== 'all' && entry.category !== category) return false;
            if (entry.price < minPrice || entry.price > maxPrice) return false;
            return true;
        });

        filtered.forEach(entry => {
            entry.distanceKm = mapState.userCoords ? getDistanceKm(mapState.userCoords, entry.coords) : null;
        });

        if (mapState.userCoords) {
            filtered.sort((a, b) => {
                const d1 = Number.isFinite(a.distanceKm) ? a.distanceKm : Number.MAX_SAFE_INTEGER;
                const d2 = Number.isFinite(b.distanceKm) ? b.distanceKm : Number.MAX_SAFE_INTEGER;
                return d1 - d2;
            });
        } else {
            filtered.sort((a, b) => a.index - b.index);
        }

        mapState.visibleEntries = filtered;
        markerLayer.clearLayers();
        filtered.forEach(entry => markerLayer.addLayer(entry.marker));
        updateSidebar(filtered);

        if (options.fit) fitToEntries(filtered);
    }

    function hydratePriceRange(entries) {
        if (!priceMinInput || !priceMaxInput) return;
        const prices = entries
            .map(entry => Number(entry.price))
            .filter(value => Number.isFinite(value) && value >= 0);

        const computedMax = prices.length ? Math.max(...prices) : 1000;
        const roundedMax = Math.max(500, Math.ceil(computedMax / 100) * 100);

        priceMinInput.min = '0';
        priceMinInput.max = String(roundedMax);
        priceMinInput.value = '0';

        priceMaxInput.min = '0';
        priceMaxInput.max = String(roundedMax);
        priceMaxInput.value = String(roundedMax);

        refreshPriceLabels();
    }

    let userLocationMarker = null;
    function centerToNearMe() {
        if (!navigator.geolocation) {
            showToast('Geolocation is not supported in this browser.', 'error');
            return;
        }
        const previousLabel = nearMeBtn?.innerText || 'Near Me';
        if (nearMeBtn) {
            nearMeBtn.disabled = true;
            nearMeBtn.innerText = 'Locating...';
        }

        navigator.geolocation.getCurrentPosition(
            position => {
                mapState.userCoords = [position.coords.latitude, position.coords.longitude];
                if (!userLocationMarker) {
                    userLocationMarker = L.circleMarker(mapState.userCoords, {
                        radius: 8,
                        color: '#166534',
                        fillColor: '#22c55e',
                        fillOpacity: 0.9,
                        weight: 2
                    }).addTo(map);
                    userLocationMarker.bindPopup('You are here');
                } else {
                    userLocationMarker.setLatLng(mapState.userCoords);
                }

                map.flyTo(mapState.userCoords, 10, { duration: 0.8 });
                applyMapFilters();

                if (nearMeBtn) {
                    nearMeBtn.classList.add('ring-2', 'ring-emerald-300');
                    nearMeBtn.innerText = 'Near Me ✓';
                    nearMeBtn.disabled = false;
                }
            },
            () => {
                showToast('Location access denied. Please allow location and try again.', 'error');
                if (nearMeBtn) {
                    nearMeBtn.innerText = previousLabel;
                    nearMeBtn.disabled = false;
                }
            },
            { enableHighAccuracy: true, timeout: 12000 }
        );
    }

    function addLegendControl() {
        const legend = L.control({ position: 'bottomleft' });
        legend.onAdd = function () {
            const div = L.DomUtil.create('div', 'kc-legend');
            div.innerHTML = `
                <div class="font-semibold text-slate-700 mb-1">Crop Categories</div>
                <div><span class="kc-dot veg"></span>Vegetables</div>
                <div><span class="kc-dot fruit"></span>Fruits</div>
                <div><span class="kc-dot grain"></span>Grains</div>
                <div><span class="kc-dot" style="background:#166534"></span>Other</div>
            `;
            return div;
        };
        legend.addTo(map);
    }

    function syncSidebarClasses() {
        if (!sidebar) return;
        const isMobile = window.innerWidth < 768;
        if (isMobile) {
            sidebar.classList.remove('closed-desktop');
            sidebar.classList.remove('mobile-hidden', 'mobile-open');
            sidebar.classList.add(mapState.sidebarMobileOpen ? 'mobile-open' : 'mobile-hidden');
            if (mapShell) mapShell.classList.remove('sidebar-collapsed');
        } else {
            sidebar.classList.remove('mobile-hidden', 'mobile-open');
            if (mapState.sidebarDesktopCollapsed) {
                sidebar.classList.add('closed-desktop');
                if (mapShell) mapShell.classList.add('sidebar-collapsed');
            } else {
                sidebar.classList.remove('closed-desktop');
                if (mapShell) mapShell.classList.remove('sidebar-collapsed');
            }
        }
    }

    function toggleSidebar() {
        if (window.innerWidth < 768) {
            mapState.sidebarMobileOpen = !mapState.sidebarMobileOpen;
        } else {
            mapState.sidebarDesktopCollapsed = !mapState.sidebarDesktopCollapsed;
        }
        syncSidebarClasses();
        setTimeout(() => map.invalidateSize(), 250);
    }

    if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
    window.addEventListener('resize', () => {
        syncSidebarClasses();
        setTimeout(() => map.invalidateSize(), 250);
    });
    syncSidebarClasses();

    if (categorySelect) {
        categorySelect.addEventListener('change', () => applyMapFilters());
    }
    if (priceMinInput) {
        priceMinInput.addEventListener('input', () => {
            clampPriceRange('min');
            applyMapFilters();
        });
    }
    if (priceMaxInput) {
        priceMaxInput.addEventListener('input', () => {
            clampPriceRange('max');
            applyMapFilters();
        });
    }
    if (nearMeBtn) nearMeBtn.addEventListener('click', centerToNearMe);
    if (recenterBtn) {
        recenterBtn.addEventListener('click', () => {
            fitToEntries(mapState.visibleEntries);
        });
    }
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', () => {
            if (categorySelect) categorySelect.value = 'all';
            mapState.userCoords = null;
            if (userLocationMarker) {
                map.removeLayer(userLocationMarker);
                userLocationMarker = null;
            }
            if (nearMeBtn) {
                nearMeBtn.classList.remove('ring-2', 'ring-emerald-300');
                nearMeBtn.innerText = 'Near Me';
                nearMeBtn.disabled = false;
            }
            hydratePriceRange(mapState.entries);
            applyMapFilters({ fit: true });
        });
    }

    addLegendControl();
    setLoading(true);

    fetch(`${API_BASE}/products`)
        .then(res => {
            if (!res.ok) throw new Error(`Failed to load products (${res.status})`);
            return res.json();
        })
        .then(products => {
            const list = Array.isArray(products) ? products : [];
            mapState.entries = list.map((product, index) => {
                const seed = `${product?._id || product?.id || product?.name || 'product'}-${index}`;
                const category = getCategoryBucket(product);
                const coords = resolveCoords(product, seed);
                const marker = L.marker(coords, {
                    icon: createMarkerIcon(category),
                    title: toSafeText(product?.name, 'Fresh Produce')
                });
                const entry = {
                    index,
                    product,
                    category,
                    coords,
                    marker,
                    price: parsePrice(product?.price),
                    quantity: getQuantity(product),
                    distanceKm: null
                };
                marker.bindPopup(popupMarkup(entry), { maxWidth: 290 });
                return entry;
            });

            hydratePriceRange(mapState.entries);
            applyMapFilters({ fit: true });
        })
        .catch(error => {
            console.error(error);
            showToast('Unable to load product map right now. Please try again.', 'error');
            updateSidebar([]);
            fitToEntries([]);
        })
        .finally(() => {
            setLoading(false);
        });
}
