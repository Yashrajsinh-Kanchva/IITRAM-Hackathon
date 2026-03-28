const API_BASE = "/api";

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
    });
}

function updateCartBadge() {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) return;

    fetch(`${API_BASE}/cart/${user.id}`)
    .then(res => res.json())
    .then(data => {
        const count = data.items ? data.items.length : 0;
        const badge = document.getElementById('cart-badge');
        if (badge) badge.innerText = count;
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
                    <h3 class="product-name">${neg.product_name}</h3>
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
            const safeName = p.name.replace(/'/g, "\\'");
            
            card.innerHTML = `
                <button class="wishlist-btn active" onclick="toggleWishlist('${p._id}', this)">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </button>
                <img src="${p.image_url}" class="product-image" onclick="window.location.href='product.html?id=${p._id}'">
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
    if (/(tomato|onion|potato|brinjal|eggplant|cabbage|carrot|cauliflower|peas|vegetable)/.test(text)) return 'vegetable';
    return '';
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
        
        card.innerHTML = `
            <button class="wishlist-btn ${isWishlisted ? 'active' : ''}" onclick="toggleWishlist('${p._id}', this)">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </button>
            <img src="${p.image_url}" class="product-image" onclick="window.location.href='product.html?id=${p._id}'">
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

            document.getElementById('p-image').src = p.image_url;
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
                card.innerHTML = `
                    <img src="${item.image}" class="cart-img">
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
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:1rem; margin-bottom:1rem">
                    <div>
                        <span style="font-weight:700">Order ID: #${order._id.slice(-6).toUpperCase()}</span>
                        <div style="color:var(--neutral-mid); font-size:12px">${new Date(order.created_at).toLocaleString()}</div>
                    </div>
                    <div class="product-badge badge-organic" style="position:static">${order.status.toUpperCase()}</div>
                </div>
                <div>
                    ${order.items.map(item => `
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px">
                            <span>${item.name} x ${item.quantity}</span>
                            <span>₹${item.price * item.quantity}</span>
                        </div>
                    `).join('')}
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
    updateCartBadge();
    const user = JSON.parse(localStorage.getItem("user"));
    const authLink = document.getElementById('auth-link');
    if (user && authLink) {
        const initial = user.name.charAt(0).toUpperCase();
        authLink.innerHTML = `<a href="profile.html" class="navbar-avatar" title="${user.name} Profile">${initial}</a>`;
    }
});
// 🗺️ Map Discovery Logic
function initMapView() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Center on Gujarat region (Agricultural Hub)
    const map = L.map('map').setView([22.3094, 72.1362], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Common Indian Town Coordinates for Geocoding Simulation
    const geoMap = {
        "Anand": [22.5645, 72.9289],
        "Surat": [21.1702, 72.8311],
        "Rajkot": [22.3039, 70.8022],
        "Ahmedabad": [23.0225, 72.5714],
        "Mehsana": [23.5880, 72.3693],
        "Amreli": [21.5974, 71.2170],
        "Bhavnagar": [21.7645, 72.1519]
    };

    fetch(`${API_BASE}/products`)
    .then(res => res.json())
    .then(products => {
        products.forEach(p => {
            let coords = geoMap[p.farmer.location];
            
            // If location not in map, generate random offset around Gujarat for visual variety
            if (!coords) {
                coords = [
                    22.3094 + (Math.random() - 0.5) * 2,
                    72.1362 + (Math.random() - 0.5) * 2
                ];
            }

            const marker = L.marker(coords).addTo(map);
            marker.bindPopup(`
                <div style="width: 200px">
                    <img src="${p.image_url}" style="width:100%; height:120px; object-fit:cover; border-radius:8px; margin-bottom:8px">
                    <b style="display:block; margin-bottom:4px">${p.name}</b>
                    <div style="font-size:12px; color:var(--neutral-mid); margin-bottom:8px">🧑‍🌾 ${p.farmer.name} • ${p.farmer.location}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center">
                        <span style="font-weight:700; color:var(--primary)">₹${p.price}</span>
                        <a href="product.html?id=${p._id}" style="font-size:12px; color:var(--accent); font-weight:700; text-decoration:none">View Details →</a>
                    </div>
                </div>
            `);
        });
    });
}
