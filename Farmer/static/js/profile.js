/* ── profile.js — KrishiConnect Farmer Profile Setup ── */

let currentStep = 1;
const TOTAL_STEPS = 3;

const stepLabels = [
  "Step 1 of 3 — Personal Info",
  "Step 2 of 3 — Farm Details",
  "Step 3 of 3 — Payment Info",
];

// ─── Navigation ────────────────────────────────────────────────────────────────

function goTo(step, goingBack = false) {
  if (!validateStep(currentStep)) return;

  const prev = document.getElementById(`step${currentStep}`);
  const next = document.getElementById(`step${step}`);

  prev.classList.remove("active");
  if (goingBack) next.classList.add("going-back");
  else next.classList.remove("going-back");

  next.classList.add("active");

  // Remove going-back after animation
  if (goingBack) setTimeout(() => next.classList.remove("going-back"), 400);

  currentStep = step;
  updateProgress();
  updateStepper();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Override "back" calls
document.querySelectorAll(".btn-back").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const targetStep = parseInt(btn.getAttribute("onclick").match(/\d+/)[0]);
    goTo(targetStep, true);
  });
});

// ─── Progress bar ──────────────────────────────────────────────────────────────

function updateProgress() {
  const fill = document.getElementById("progressFill");
  const text = document.getElementById("progressText");
  fill.style.width = `${(currentStep / TOTAL_STEPS) * 100}%`;
  text.textContent = stepLabels[currentStep - 1];
}

// ─── Step indicators ──────────────────────────────────────────────────────────

function updateStepper() {
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const item = document.getElementById(`si-${i}`);
    item.classList.remove("active", "done");
    if (i === currentStep) item.classList.add("active");
    if (i < currentStep) item.classList.add("done");
  }
  // Update connectors
  for (let i = 1; i < TOTAL_STEPS; i++) {
    const conn = document.getElementById(`sc-${i}`);
    if (conn) {
      conn.classList.toggle("done", i < currentStep);
    }
  }
}

// ─── Validation ────────────────────────────────────────────────────────────────

function clearErr(id) {
  const el = document.getElementById(id);
  if (el) el.textContent = "";
}
function setErr(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
}
function shake(fieldId) {
  const box = document.getElementById(fieldId)?.closest(".input-box") ||
               document.getElementById(fieldId);
  if (!box) return;
  box.style.animation = "shake .3s ease";
  setTimeout(() => (box.style.animation = ""), 320);
}

function validateStep(step) {
  let ok = true;

  if (step === 1) {
    ["nameErr", "villageErr", "cityErr", "stateErr", "pincodeErr"].forEach(clearErr);

    const name    = document.getElementById("name").value.trim();
    const village = document.getElementById("village").value.trim();
    const city    = document.getElementById("city").value.trim();
    const state   = document.getElementById("state").value;
    const pincode = document.getElementById("pincode").value.trim();

    if (!name)    { setErr("nameErr",    "Full name is required"); shake("name"); ok = false; }
    if (!village) { setErr("villageErr", "Village is required");   shake("village"); ok = false; }
    if (!city)    { setErr("cityErr",    "City is required");       shake("city"); ok = false; }
    if (!state)   { setErr("stateErr",   "Please select a state");  ok = false; }
    if (!pincode || !/^\d{6}$/.test(pincode)) {
      setErr("pincodeErr", "Enter a valid 6-digit pincode");
      shake("pincode");
      ok = false;
    }
  }

  if (step === 2) {
    clearErr("cropErr");
    const selected = getSelectedCrops();
    if (selected.length === 0) {
      setErr("cropErr", "Select at least one crop type");
      ok = false;
    }
  }

  if (step === 3) {
    ["accHolderErr", "accNumberErr", "ifscErr"].forEach(clearErr);

    const holder = document.getElementById("accHolder").value.trim();
    const accNum = document.getElementById("accNumber").value.trim();
    const ifsc   = document.getElementById("ifsc").value.trim();

    if (!holder) { setErr("accHolderErr", "Account holder name is required"); shake("accHolder"); ok = false; }
    if (!accNum || accNum.length < 9) { setErr("accNumberErr", "Enter a valid account number"); shake("accNumber"); ok = false; }
    if (!ifsc || !/^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc.toUpperCase())) {
      setErr("ifscErr", "Enter a valid IFSC code (e.g. SBIN0001234)");
      shake("ifsc");
      ok = false;
    }
  }

  return ok;
}

// ─── Crop helpers ─────────────────────────────────────────────────────────────

function getSelectedCrops() {
  return [...document.querySelectorAll("#cropGrid input:checked")].map((cb) => cb.value);
}

function addCustomCrop() {
  const input = document.getElementById("customCrop");
  const val = input.value.trim();
  if (!val) return;

  const grid = document.getElementById("cropGrid");

  // Avoid duplicates
  const already = [...grid.querySelectorAll("input")].some(
    (cb) => cb.value.toLowerCase() === val.toLowerCase()
  );
  if (already) {
    input.style.borderColor = "var(--error)";
    setTimeout(() => (input.style.borderColor = ""), 1200);
    return;
  }

  const label = document.createElement("label");
  label.className = "crop-pill";
  label.innerHTML = `<input type="checkbox" value="${val}" checked /><span>🌿 ${val}</span>`;
  grid.appendChild(label);
  input.value = "";
  input.focus();
}

// Allow Enter key to add custom crop
document.getElementById("customCrop")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); addCustomCrop(); }
});

// IFSC auto-uppercase
document.getElementById("ifsc")?.addEventListener("input", function () {
  this.value = this.value.toUpperCase();
});

// Pincode – numbers only
document.getElementById("pincode")?.addEventListener("input", function () {
  this.value = this.value.replace(/\D/g, "").slice(0, 6);
});

// Account number – numbers only
document.getElementById("accNumber")?.addEventListener("input", function () {
  this.value = this.value.replace(/\D/g, "").slice(0, 18);
});

// ─── Submit ────────────────────────────────────────────────────────────────────

async function submitProfile() {
  if (!validateStep(3)) return;

  const submitBtn = document.getElementById("submitBtn");
  const btnText   = document.getElementById("btnText");
  const btnLoader = document.getElementById("btnLoader");

  submitBtn.disabled = true;
  btnText.style.display  = "none";
  btnLoader.style.display = "inline";

  const payload = {
    // Step 1
    name:    document.getElementById("name").value.trim(),
    village: document.getElementById("village").value.trim(),
    city:    document.getElementById("city").value.trim(),
    state:   document.getElementById("state").value,
    pincode: document.getElementById("pincode").value.trim(),
    // Step 2
    crop_types:      getSelectedCrops(),
    farm_size:       document.getElementById("farmSize").value || null,
    farm_size_unit:  document.getElementById("farmSizeUnit").value,
    // Step 3
    bank_acc_holder: document.getElementById("accHolder").value.trim(),
    bank_acc_number: document.getElementById("accNumber").value.trim(),
    bank_ifsc:       document.getElementById("ifsc").value.trim().toUpperCase(),
    bank_name:       document.getElementById("bankName").value.trim(),
    upi_id:          document.getElementById("upiId").value.trim(),
  };

  try {
    const res  = await fetch("/farmer/profile-setup", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.success) {
      showSuccess(data.redirect);
    } else {
      alert("❌ " + (data.error || "Something went wrong. Please try again."));
      submitBtn.disabled = false;
      btnText.style.display   = "inline";
      btnLoader.style.display = "none";
    }
  } catch (err) {
    alert("❌ Network error. Please check your connection.");
    submitBtn.disabled = false;
    btnText.style.display   = "inline";
    btnLoader.style.display = "none";
  }
}

// ─── Success animation ────────────────────────────────────────────────────────

function showSuccess(redirectUrl) {
  const overlay = document.getElementById("successOverlay");
  overlay.classList.add("show");

  // Auto-redirect after 4 seconds
  setTimeout(() => {
    window.location.href = redirectUrl || "/farmer/dashboard";
  }, 4000);
}

// ─── Shake animation (CSS injected) ──────────────────────────────────────────

const shakeStyle = document.createElement("style");
shakeStyle.textContent = `
  @keyframes shake {
    0%,100%{ transform:translateX(0); }
    20%     { transform:translateX(-6px); }
    40%     { transform:translateX(6px); }
    60%     { transform:translateX(-4px); }
    80%     { transform:translateX(4px); }
  }
`;
document.head.appendChild(shakeStyle);

// ─── Init ─────────────────────────────────────────────────────────────────────
updateProgress();
updateStepper();
