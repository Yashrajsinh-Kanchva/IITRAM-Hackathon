/* ── product.js — Add Product form logic ── */

// ─── Price type toggle ────────────────────────────────────────────────────────
function setPriceType(type) {
  document.getElementById("priceType").value = type;

  const btnFixed = document.getElementById("btnFixed");
  const btnNego  = document.getElementById("btnNego");
  const fixedBox = document.getElementById("fixedPriceBox");
  const negoBox  = document.getElementById("negoBox");

  if (type === "fixed") {
    btnFixed.classList.add("active");
    btnNego.classList.remove("active");
    fixedBox.style.display = "flex";
    negoBox.style.display  = "none";
  } else {
    btnNego.classList.add("active");
    btnFixed.classList.remove("active");
    fixedBox.style.display = "none";
    negoBox.style.display  = "block";
    document.getElementById("priceErr").textContent = "";
  }
}

// Keep "per unit" label in sync with quantity unit
document.getElementById("quantityUnit")?.addEventListener("change", function () {
  document.getElementById("perUnitLabel").textContent = this.value;
  // mirror unit to minOrder unit
  document.getElementById("minOrderUnit").value = this.value;
});

// ─── Image upload / drag-and-drop ─────────────────────────────────────────────
const zone = document.getElementById("imageUploadZone");

zone?.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("drag-over"); });
zone?.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
zone?.addEventListener("drop", (e) => {
  e.preventDefault();
  zone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) previewImage(file);
});
zone?.addEventListener("click", (e) => {
  if (e.target.closest(".btn-remove-img") || e.target.closest(".btn-upload-trigger")) return;
  document.getElementById("imageInput").click();
});

function handleImageChange(event) {
  const file = event.target.files[0];
  if (file) previewImage(file);
}

function previewImage(file) {
  const allowed = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
  if (!allowed.includes(file.type)) {
    alert("Please upload a JPG, PNG or WEBP image.");
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = document.getElementById("imagePreview");
    const placeholder = document.getElementById("uploadPlaceholder");
    const removeBtn = document.getElementById("removeImgBtn");
    preview.src = e.target.result;
    preview.style.display = "block";
    placeholder.style.display = "none";
    removeBtn.style.display = "block";
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  document.getElementById("imagePreview").style.display = "none";
  document.getElementById("uploadPlaceholder").style.display = "flex";
  document.getElementById("removeImgBtn").style.display = "none";
  document.getElementById("imageInput").value = "";
}

// ─── Validation ───────────────────────────────────────────────────────────────
function clr(id) { const e = document.getElementById(id); if (e) e.textContent = ""; }
function setErr(id, msg) { const e = document.getElementById(id); if (e) e.textContent = msg; }
function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatInr(value) {
  const n = Number(value || 0);
  return Number.isFinite(n)
    ? n.toLocaleString("en-IN", { maximumFractionDigits: 2 })
    : "0";
}

function renderMarketPriceHint(data, requestedCrop) {
  const box = document.getElementById("marketPriceAssist");
  if (!box) return;

  if (!data) {
    box.className = "market-price-assist";
    box.innerHTML = "";
    return;
  }

  if (data.loading) {
    box.className = "market-price-assist show loading";
    box.innerHTML = `<div class="mp-line">Checking current market price...</div>`;
    return;
  }

  if (!data.success) {
    box.className = "market-price-assist show";
    box.innerHTML = `<div class="mp-line">Could not fetch market price right now.</div>`;
    return;
  }

  if (!data.has_data) {
    box.className = "market-price-assist show";
    box.innerHTML = `
      <div class="mp-title">Market Price</div>
      <div class="mp-line">No recent data found for "${escapeHtml(requestedCrop)}".</div>
      <div class="mp-meta">Try a more specific crop name like "Tomato" or "Wheat".</div>
    `;
    return;
  }

  box.className = "market-price-assist show";
  box.innerHTML = `
    <div class="mp-title">Current Market Price (Estimate)</div>
    <div class="mp-line">₹${formatInr(data.suggested_price)} per ${escapeHtml(data.unit_hint || "kg")}</div>
    <div class="mp-meta">Range: ₹${formatInr(data.min_price)} - ₹${formatInr(data.max_price)} · ${data.sample_size} recent listings</div>
    <div class="mp-actions">
      <button type="button" class="mp-btn" id="applyMarketPriceBtn">Use this price</button>
      <span class="mp-meta">${escapeHtml(data.message || "")}</span>
    </div>
  `;

  document.getElementById("applyMarketPriceBtn")?.addEventListener("click", () => {
    setPriceType("fixed");
    const priceInput = document.getElementById("price");
    if (priceInput) {
      priceInput.value = String(data.suggested_price || "");
      priceInput.focus();
      priceInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
}

let marketPriceDebounceTimer = null;
let marketPriceRequestSeq = 0;

async function fetchMarketPriceHint(cropName) {
  const requestedCrop = String(cropName || "").trim();
  if (requestedCrop.length < 2) {
    renderMarketPriceHint(null);
    return;
  }

  const requestId = ++marketPriceRequestSeq;
  renderMarketPriceHint({ loading: true });

  try {
    const res = await fetch(`/farmer/api/market-price?crop_name=${encodeURIComponent(requestedCrop)}`);
    const data = await res.json();
    if (requestId !== marketPriceRequestSeq) return;
    renderMarketPriceHint(data, requestedCrop);
  } catch (err) {
    if (requestId !== marketPriceRequestSeq) return;
    renderMarketPriceHint({ success: false }, requestedCrop);
  }
}

document.getElementById("cropName")?.addEventListener("input", (event) => {
  const value = event.target.value || "";
  window.clearTimeout(marketPriceDebounceTimer);
  marketPriceDebounceTimer = window.setTimeout(() => {
    fetchMarketPriceHint(value);
  }, 350);
});

document.getElementById("cropName")?.addEventListener("blur", (event) => {
  const value = event.target.value || "";
  if (String(value).trim().length >= 2) {
    fetchMarketPriceHint(value);
  }
});

function validate() {
  let ok = true;
  ["cropNameErr","quantityErr","priceErr","harvestDateErr","minOrderErr"].forEach(clr);

  if (!document.getElementById("cropName").value.trim()) {
    setErr("cropNameErr", "Crop name is required"); ok = false;
  }
  if (!document.getElementById("quantity").value || parseFloat(document.getElementById("quantity").value) <= 0) {
    setErr("quantityErr", "Enter a valid quantity"); ok = false;
  }
  const priceType = document.getElementById("priceType").value;
  if (priceType === "fixed") {
    const p = document.getElementById("price").value;
    if (!p || parseFloat(p) <= 0) { setErr("priceErr", "Enter a valid price per unit"); ok = false; }
  }
  if (!document.getElementById("harvestDate").value) {
    setErr("harvestDateErr", "Harvest date is required"); ok = false;
  }
  if (!document.getElementById("minOrderQty").value || parseFloat(document.getElementById("minOrderQty").value) <= 0) {
    setErr("minOrderErr", "Minimum order quantity is required"); ok = false;
  }
  return ok;
}

// ─── Submit ───────────────────────────────────────────────────────────────────
async function submitProduct() {
  if (!validate()) return;

  const btn    = document.getElementById("submitBtn");
  const btnTxt = document.getElementById("btnText");
  const loader = document.getElementById("btnLoader");
  btn.disabled = true;
  btnTxt.style.display = "none";
  loader.style.display = "inline";

  const formData = new FormData();
  formData.append("crop_name",      document.getElementById("cropName").value.trim());
  formData.append("quantity",       document.getElementById("quantity").value);
  formData.append("quantity_unit",  document.getElementById("quantityUnit").value);
  formData.append("price_type",     document.getElementById("priceType").value);
  formData.append("price",          document.getElementById("price")?.value || "");
  formData.append("harvest_date",   document.getElementById("harvestDate").value);
  formData.append("min_order_qty",  document.getElementById("minOrderQty").value);
  formData.append("min_order_unit", document.getElementById("minOrderUnit").value);

  const imageFile = document.getElementById("imageInput").files[0];
  if (imageFile) formData.append("image", imageFile);

  try {
    const res  = await fetch("/farmer/add-product", { method: "POST", body: formData });
    const data = await res.json();

    if (data.success) {
      // Show success toast
      const toast = document.getElementById("successToast");
      toast.classList.add("show");
      setTimeout(() => {
        window.location.href = data.redirect || "/farmer/dashboard";
      }, 2000);
    } else {
      // Show field-level errors if returned
      if (data.errors) {
        Object.entries(data.errors).forEach(([field, msg]) => {
          const map = {
            crop_name: "cropNameErr", quantity: "quantityErr",
            price: "priceErr", harvest_date: "harvestDateErr",
            min_order_qty: "minOrderErr"
          };
          if (map[field]) setErr(map[field], msg);
        });
      } else {
        alert("❌ " + (data.error || "Something went wrong"));
      }
      btn.disabled = false;
      btnTxt.style.display = "inline";
      loader.style.display = "none";
    }
  } catch (err) {
    alert("❌ Network error — check your connection");
    btn.disabled = false;
    btnTxt.style.display = "inline";
    loader.style.display = "none";
  }
}

// Set min date = today on harvest date picker
const hd = document.getElementById("harvestDate");
if (hd) hd.min = new Date().toISOString().split("T")[0];
