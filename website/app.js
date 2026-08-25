/**
 * Logistics ResolveR - Kinetic Typography, Draggable Slider, Route Simulation & Parser
 */

const KINETIC_PHRASES = [
  "Standardized Shipping Labels.",
  "Sub-8ms Geocoded Coordinates.",
  "Zero-RTO Dispatch Records.",
  "Validated Postal PIN Sequences."
];

const PRESETS = {
  indian_messy: "flat 402 shri krishna apts opp hdfc bank m g road indiranagar bangalore karnataka 560038",
  landmark_typo: "h no 12/b 2nd flr nr metro piller 45 laxmi ngr new delhi 110092",
  ecommerce_note: "Deliver behind Apollo pharmacy, Plot 88 Sector 14 Vashi Navi Mumbai MH 400703",
  global_standard: "Suite 300 742 Evergreen Terrace Springfield OR 97477 USA"
};

const LANDMARK_MARKERS = ["opp", "opposite", "near", "nr", "behind", "bh", "beside", "adj", "adjacent", "facing", "next to", "above", "below", "pillar", "piller", "gate"];
const NUMBER_MARKERS = ["flat", "apt", "apts", "apartment", "h", "house", "plot", "door", "no", "room", "flr", "floor", "suite", "ste", "bldg", "building", "unit", "block"];
const STREET_MARKERS = ["road", "rd", "street", "st", "lane", "ln", "avenue", "ave", "marg", "cross", "main", "sector", "sec", "nagar", "ngr", "colony", "layout", "vihar", "enclave", "extension", "ext", "terrace", "blvd", "boulevard"];
const STATES = ["karnataka", "maharashtra", "delhi", "tamil nadu", "telangana", "gujarat", "uttar pradesh", "rajasthan", "west bengal", "kerala", "mh", "ka", "dl", "tn", "ts", "gj", "up", "or", "ca", "ny", "tx", "fl"];
const CITIES = ["bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "chennai", "hyderabad", "pune", "ahmedabad", "kolkata", "jaipur", "vashi", "navi mumbai", "springfield", "indiranagar", "noida", "gurgaon", "gurugram"];

const TAG_NAMES = {
  N: "Number",
  S: "Street",
  L: "Landmark",
  C: "City",
  A: "State",
  P: "Pincode",
  O: "Other"
};

/* ==========================================================================
   1. KINETIC TYPOGRAPHY PAGE INTRO REVEALER
   ========================================================================== */
function initKineticTypography() {
  const el = document.getElementById("kineticTarget");
  if (!el) return;

  let phraseIdx = 0;
  let charIdx = 0;
  let isDeleting = false;

  function typeStep() {
    const currentPhrase = KINETIC_PHRASES[phraseIdx];

    if (isDeleting) {
      el.textContent = currentPhrase.substring(0, charIdx - 1);
      charIdx--;
    } else {
      el.textContent = currentPhrase.substring(0, charIdx + 1);
      charIdx++;
    }

    let speed = isDeleting ? 30 : 65;

    if (!isDeleting && charIdx === currentPhrase.length) {
      speed = 3000; // Hold full sentence
      isDeleting = true;
    } else if (isDeleting && charIdx === 0) {
      isDeleting = false;
      phraseIdx = (phraseIdx + 1) % KINETIC_PHRASES.length;
      speed = 400;
    }

    setTimeout(typeStep, speed);
  }

  typeStep();
}

/* ==========================================================================
   2. THE CUTE BEFORE / AFTER TRANSFORMER SLIDER (DRAGGABLE CARD)
   ========================================================================== */
function initTransformerSlider() {
  const container = document.getElementById("splitSliderContainer");
  const divider = document.getElementById("splitDivider");
  if (!container || !divider) return;

  let isDragging = false;

  function updatePos(clientX) {
    const rect = container.getBoundingClientRect();
    let x = clientX - rect.left;
    x = Math.max(30, Math.min(x, rect.width - 30));
    const percentage = (x / rect.width) * 100;
    container.style.setProperty("--split-pos", `${percentage}%`);
  }

  divider.addEventListener("mousedown", (e) => {
    isDragging = true;
    e.preventDefault();
  });
  window.addEventListener("mouseup", () => isDragging = false);
  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    updatePos(e.clientX);
  });

  // Touch Support for Mobile
  divider.addEventListener("touchstart", (e) => {
    isDragging = true;
  });
  window.addEventListener("touchend", () => isDragging = false);
  window.addEventListener("touchmove", (e) => {
    if (!isDragging || !e.touches[0]) return;
    updatePos(e.touches[0].clientX);
  });
}

/* ==========================================================================
   3. ANIMATED DELIVERY TRUCK ROUTE SIMULATION
   ========================================================================== */
let routeAnimFrame = null;

function initRouteSimulator() {
  const btnFailed = document.getElementById("btnRouteFailed");
  const btnOptimized = document.getElementById("btnRouteOptimized");
  const truckMarker = document.getElementById("truckMarker");
  const pathFailed = document.getElementById("pathFailed");
  const pathOptimized = document.getElementById("pathOptimized");
  const routeStatusText = document.getElementById("routeStatusText");
  const routeMetricDist = document.getElementById("routeMetricDist");
  const routeMetricTime = document.getElementById("routeMetricTime");

  if (!btnFailed || !btnOptimized || !truckMarker) return;

  function runTruck(pathEl, isOptimized) {
    if (!pathEl) return;
    const pathLength = pathEl.getTotalLength();
    let start = null;
    const duration = isOptimized ? 3000 : 6000;

    if (routeAnimFrame) cancelAnimationFrame(routeAnimFrame);

    function step(timestamp) {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const point = pathEl.getPointAtLength(progress * pathLength);
      
      truckMarker.setAttribute("transform", `translate(${point.x - 12}, ${point.y - 12})`);

      if (progress < 1) {
        routeAnimFrame = requestAnimationFrame(step);
      } else {
        start = null;
        routeAnimFrame = requestAnimationFrame(step);
      }
    }

    routeAnimFrame = requestAnimationFrame(step);
  }

  btnFailed.addEventListener("click", () => {
    btnFailed.className = "route-btn active-red";
    btnOptimized.className = "route-btn";
    pathFailed.style.display = "block";
    pathOptimized.style.display = "none";
    
    routeStatusText.innerHTML = '<span style="color: #F87171;">⚠️ Delivery Failure:</span> Driver stranded searching for ambiguous landmark.';
    routeMetricDist.textContent = "14.2 km (Lost Loop)";
    routeMetricTime.textContent = "48 mins (RTO Fail)";
    runTruck(pathFailed, false);
  });

  btnOptimized.addEventListener("click", () => {
    btnOptimized.className = "route-btn active-green";
    btnFailed.className = "route-btn";
    pathFailed.style.display = "none";
    pathOptimized.style.display = "block";
    
    routeStatusText.innerHTML = '<span style="color: #34D399;">✓ Direct Success:</span> Address structured & geocoded straight to customer door.';
    routeMetricDist.textContent = "3.8 km (Optimized)";
    routeMetricTime.textContent = "8 mins (Delivered)";
    runTruck(pathOptimized, true);
  });

  // Start in optimized state
  btnOptimized.click();
}

/* ==========================================================================
   4. ADDRESS PARSER ENGINE SIMULATOR
   ========================================================================== */
function parseAddress(rawText) {
  const startTime = performance.now();
  if (!rawText || !rawText.trim()) {
    return {
      tokens: [],
      components: { number: "—", street: "—", landmark: "—", city: "—", state: "—", pincode: "—" },
      stats: { latency: "0.0 ms", confidence: "0.0%", tokenCount: 0 }
    };
  }

  const cleanStr = rawText.replace(/[,\/#!$%\^&\*;:{}=\-_`~()]/g, " ").replace(/\s+/g, " ").trim();
  const words = cleanStr.split(" ");
  const taggedTokens = [];

  let isLandmarkContext = false;
  let isNumberContext = false;

  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    const lower = word.toLowerCase();
    let tag = "O";

    if (/^\d{6}$/.test(word) || /^\d{5}$/.test(word)) {
      tag = "P";
      isLandmarkContext = false;
      isNumberContext = false;
    } else if (LANDMARK_MARKERS.includes(lower)) {
      tag = "L";
      isLandmarkContext = true;
      isNumberContext = false;
    } else if (isLandmarkContext) {
      if (STREET_MARKERS.includes(lower) || CITIES.includes(lower) || STATES.includes(lower)) {
        isLandmarkContext = false;
      } else {
        tag = "L";
      }
    }

    if (tag === "O") {
      if (NUMBER_MARKERS.includes(lower) || (/\d+/.test(word) && !/^\d{5,6}$/.test(word))) {
        tag = "N";
        isNumberContext = true;
      } else if (isNumberContext && !STREET_MARKERS.includes(lower) && !CITIES.includes(lower) && !STATES.includes(lower)) {
        tag = "N";
      } else {
        isNumberContext = false;
      }
    }

    if (tag === "O") {
      if (STATES.includes(lower)) {
        tag = "A";
      } else if (CITIES.includes(lower)) {
        tag = "C";
      } else if (STREET_MARKERS.includes(lower)) {
        tag = "S";
      } else {
        if (i > 0 && taggedTokens[i - 1].tag === "S" && !CITIES.includes(lower) && !STATES.includes(lower)) {
          tag = "S";
        } else if (i > 0 && taggedTokens[i - 1].tag === "C" && !STATES.includes(lower)) {
          tag = "C";
        } else {
          tag = "S";
        }
      }
    }

    taggedTokens.push({ text: word, tag });
  }

  const components = {
    number: taggedTokens.filter(t => t.tag === "N").map(t => t.text).join(" ") || "—",
    street: taggedTokens.filter(t => t.tag === "S").map(t => t.text).join(" ") || "—",
    landmark: taggedTokens.filter(t => t.tag === "L").map(t => t.text).join(" ") || "—",
    city: taggedTokens.filter(t => t.tag === "C").map(t => t.text).join(" ") || "—",
    state: taggedTokens.filter(t => t.tag === "A").map(t => t.text).join(" ") || "—",
    pincode: taggedTokens.filter(t => t.tag === "P").map(t => t.text).join(" ") || "—"
  };

  const endTime = performance.now();
  const latency = (endTime - startTime + Math.random() * 2 + 3).toFixed(1) + " ms";
  const confidence = (96.4 + Math.random() * 3.2).toFixed(1) + "%";

  return {
    tokens: taggedTokens,
    components,
    stats: { latency, confidence, tokenCount: taggedTokens.length }
  };
}

const addressInput = document.getElementById("addressInput");
const tokenStream = document.getElementById("tokenStream");
const codePreview = document.getElementById("codePreview");
const hudLatency = document.getElementById("hudLatency");
const hudConfidence = document.getElementById("hudConfidence");
const hudTokens = document.getElementById("hudTokens");

const valNumber = document.getElementById("valNumber");
const valStreet = document.getElementById("valStreet");
const valLandmark = document.getElementById("valLandmark");
const valCity = document.getElementById("valCity");
const valState = document.getElementById("valState");
const valPincode = document.getElementById("valPincode");

function renderResults(result) {
  if (hudLatency) hudLatency.textContent = result.stats.latency;
  if (hudConfidence) hudConfidence.textContent = result.stats.confidence;
  if (hudTokens) hudTokens.textContent = result.stats.tokenCount;

  if (tokenStream) {
    tokenStream.innerHTML = "";
    if (result.tokens.length === 0) {
      tokenStream.innerHTML = '<span style="color: var(--text-dim); font-size: 0.9rem;">Type an address above to view parsed token stream...</span>';
    } else {
      result.tokens.forEach(tok => {
        const badge = document.createElement("div");
        badge.className = `tag-badge tag-${tok.tag}`;
        badge.innerHTML = `
          <span>${tok.text}</span>
          <span class="tag-type">${TAG_NAMES[tok.tag] || tok.tag}</span>
        `;
        tokenStream.appendChild(badge);
      });
    }
  }

  if (valNumber) valNumber.textContent = result.components.number;
  if (valStreet) valStreet.textContent = result.components.street;
  if (valLandmark) valLandmark.textContent = result.components.landmark;
  if (valCity) valCity.textContent = result.components.city;
  if (valState) valState.textContent = result.components.state;
  if (valPincode) valPincode.textContent = result.components.pincode;

  if (codePreview) {
    const jsonOutput = {
      status: "success",
      model: "LogisticsResolveR-CRF-v2.4",
      confidence_score: parseFloat(result.stats.confidence) / 100,
      latency_ms: parseFloat(result.stats.latency),
      parsed_address: {
        unit_or_building: result.components.number !== "—" ? result.components.number : null,
        street_or_area: result.components.street !== "—" ? result.components.street : null,
        landmark: result.components.landmark !== "—" ? result.components.landmark : null,
        city_district: result.components.city !== "—" ? result.components.city : null,
        state_province: result.components.state !== "—" ? result.components.state : null,
        postal_code: result.components.pincode !== "—" ? result.components.pincode : null
      },
      raw_tokens: result.tokens
    };
    codePreview.textContent = JSON.stringify(jsonOutput, null, 2);
  }
}

function handleInputChange() {
  if (!addressInput) return;
  const result = parseAddress(addressInput.value);
  renderResults(result);
}

function showToast(msg = "Copied to clipboard!") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = "✓ " + msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

/* 3D Tilt */
function init3DTilt() {
  const cards = document.querySelectorAll(".tilt-card");
  cards.forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -5;
      const rotateY = ((x - centerX) / centerX) * 5;
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-2px)`;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)";
    });
  });
}

/* ROI Calculator */
function animateValue(element, start, end, duration, prefix = "", suffix = "") {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const current = Math.floor(progress * (end - start) + start);
    element.textContent = prefix + current.toLocaleString() + suffix;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

let lastSavings = 0;
let lastFailures = 0;
let lastHours = 0;

function updateCalculator() {
  const volumeSlider = document.getElementById("volumeSlider");
  const failureSlider = document.getElementById("failureSlider");
  const volumeVal = document.getElementById("volumeVal");
  const failureVal = document.getElementById("failureVal");
  const totalSavingsNum = document.getElementById("totalSavingsNum");
  const savedFailuresNum = document.getElementById("savedFailuresNum");
  const savedHoursNum = document.getElementById("savedHoursNum");

  if (!volumeSlider || !failureSlider) return;

  const volume = parseInt(volumeSlider.value);
  const failureRate = parseFloat(failureSlider.value) / 100;

  volumeVal.textContent = volume.toLocaleString() + " / mo";
  failureVal.textContent = failureSlider.value + "%";

  const failedDeliveriesPerYear = volume * 12 * failureRate;
  const resolvedWithModel = failedDeliveriesPerYear * 0.9159;
  const annualSavings = Math.round(resolvedWithModel * 4.5);
  const hoursSaved = Math.round(resolvedWithModel * (15 / 60));

  animateValue(totalSavingsNum, lastSavings, annualSavings, 300, "$");
  animateValue(savedFailuresNum, lastFailures, Math.round(resolvedWithModel), 300);
  animateValue(savedHoursNum, lastHours, hoursSaved, 300, "", " hrs");

  lastSavings = annualSavings;
  lastFailures = Math.round(resolvedWithModel);
  lastHours = hoursSaved;
}

window.addEventListener("DOMContentLoaded", () => {
  initKineticTypography();
  initTransformerSlider();
  initRouteSimulator();
  init3DTilt();

  document.querySelectorAll(".preset-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const key = chip.getAttribute("data-preset");
      if (PRESETS[key] && addressInput) {
        addressInput.value = PRESETS[key];
        handleInputChange();
      }
    });
  });

  if (addressInput) {
    addressInput.value = PRESETS.indian_messy;
    addressInput.addEventListener("input", handleInputChange);
    handleInputChange();
  }

  const copyJsonBtn = document.getElementById("copyJsonBtn");
  if (copyJsonBtn && codePreview) {
    copyJsonBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(codePreview.textContent).then(() => {
        showToast("JSON payload copied to clipboard!");
      });
    });
  }

  const volumeSlider = document.getElementById("volumeSlider");
  const failureSlider = document.getElementById("failureSlider");
  if (volumeSlider && failureSlider) {
    volumeSlider.addEventListener("input", updateCalculator);
    failureSlider.addEventListener("input", updateCalculator);
    updateCalculator();
  }

  document.querySelectorAll(".faq-question").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.parentElement.classList.toggle("active");
    });
  });
});
