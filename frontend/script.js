// ============================================================
//  MovieFinder – script.js
//  Communicates with the FastAPI backend at localhost:8000
// ============================================================

const API_BASE = "http://localhost:8000";

// DOM references
const btnRecommend = document.getElementById("btn-recommend");
const btnSurprise = document.getElementById("btn-surprise");
const statusBar = document.getElementById("status-bar");
const resultsSection = document.getElementById("results-section");

// ISO 639‑1 language code → human-readable name
const LANG_NAMES = {
  ar: "Arabic", bn: "Bengali", ca: "Catalan", cn: "Chinese", cs: "Czech",
  da: "Danish", de: "German", el: "Greek", en: "English", es: "Spanish",
  et: "Estonian", eu: "Basque", fa: "Persian", fi: "Finnish", fr: "French",
  he: "Hebrew", hi: "Hindi", hu: "Hungarian", id: "Indonesian", is: "Icelandic",
  it: "Italian", ja: "Japanese", ko: "Korean", la: "Latin", lv: "Latvian",
  ml: "Malayalam", ms: "Malay", nb: "Norwegian", nl: "Dutch", no: "Norwegian",
  pl: "Polish", pt: "Portuguese", ro: "Romanian", ru: "Russian", sr: "Serbian",
  sv: "Swedish", ta: "Tamil", te: "Telugu", th: "Thai", tl: "Filipino",
  tr: "Turkish", uk: "Ukrainian", zh: "Chinese",
};

function langLabel(code) {
  return LANG_NAMES[code] || code.toUpperCase();
}

// ── Helpers ─────────────────────────────────────────────────

function showStatus(html) {
  statusBar.innerHTML = html;
}

function clearStatus() {
  statusBar.innerHTML = "";
}

function truncateText(text, maxLen = 120) {
  if (!text || text.length <= maxLen) return text || "";
  return text.substring(0, maxLen).trimEnd() + "…";
}

function buildMovieCard(movie, index) {
  const card = document.createElement("article");
  card.className = "movie-card";
  card.style.animationDelay = `${index * 0.05}s`;

  const rating = parseFloat(movie.rating).toFixed(1);
  const posterAlt = `${movie.title} poster`;
  const overview = truncateText(movie.overview, 120);
  const language = langLabel(movie.language || "");

  card.innerHTML = `
    <div class="card-poster">
      <img
        src="${escapeHtml(movie.poster_url)}"
        alt="${escapeHtml(posterAlt)}"
        loading="lazy"
        onerror="this.src='https://picsum.photos/seed/fallback/300/450'"
      />
      <div class="card-poster-overlay"></div>
      <span class="card-rating-badge">
        ⭐ ${escapeHtml(String(rating))}
      </span>
    </div>
    <div class="card-info">
      <h3 class="card-title" title="${escapeHtml(movie.title)}">${escapeHtml(movie.title)}</h3>
      <div class="card-meta">
        <span class="meta-tag">${escapeHtml(movie.genre)}</span>
        <span class="meta-tag">${escapeHtml(movie.year.toString())}</span>
        <span class="meta-tag">${escapeHtml(language)}</span>
      </div>
      ${overview ? `<p class="card-overview">${escapeHtml(overview)}</p>` : ""}
    </div>
  `;
  return card;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderResults(movies, totalFiltered) {
  resultsSection.innerHTML = "";

  if (!movies || movies.length === 0) {
    resultsSection.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h3>No movies found</h3>
        <p>No movies match your filters. Try changing or relaxing your criteria.</p>
      </div>
    `;
    return;
  }

  // Header row
  const header = document.createElement("div");
  header.className = "results-header";
  header.innerHTML = `
    <p class="results-title">
      Top Recommendations
      <span class="results-badge">${movies.length}</span>
    </p>
    <p class="status-count">
      Filtered from <strong>${totalFiltered}</strong> matching movies
    </p>
  `;
  resultsSection.appendChild(header);

  // Grid
  const grid = document.createElement("div");
  grid.className = "results-grid";

  movies.forEach((movie, i) => {
    grid.appendChild(buildMovieCard(movie, i));
  });

  resultsSection.appendChild(grid);
}

function showWelcome() {
  resultsSection.innerHTML = `
    <div class="welcome-state">
      <span class="welcome-icon">🎬</span>
      <h2>Discover Your Next Favorite Movie</h2>
      <p>Select your preferences above and hit <strong>Recommend Movies</strong> to get personalised picks powered by machine learning.</p>
      <div class="welcome-hints">
        <span class="hint-chip">🤖 KNN AI Model</span>
        <span class="hint-chip">🎭 9,800+ Movies</span>
        <span class="hint-chip">🌍 40+ Languages</span>
        <span class="hint-chip">🎯 Cosine Similarity</span>
      </div>
    </div>
  `;
}

// ── Populate dropdowns from backend ──────────────────────────

async function populateFilters() {
  try {
    const resp = await fetch(`${API_BASE}/filters`);
    if (!resp.ok) return;
    const data = await resp.json();

    // Genre dropdown
    const genreSelect = document.getElementById("filter-genre");
    (data.genres || []).forEach(g => {
      const opt = document.createElement("option");
      opt.value = g;
      opt.textContent = g;
      genreSelect.appendChild(opt);
    });

    // Language dropdown
    const langSelect = document.getElementById("filter-language");
    (data.languages || []).forEach(l => {
      const opt = document.createElement("option");
      opt.value = l;
      opt.textContent = langLabel(l);
      langSelect.appendChild(opt);
    });

    // Year range defaults
    if (data.year_min) document.getElementById("filter-year-start").value = data.year_min;
    if (data.year_max) document.getElementById("filter-year-end").value = data.year_max;
  } catch (err) {
    console.warn("Could not load filters:", err);
  }
}

// ── Build query params ───────────────────────────────────────

function buildParams() {
  const params = new URLSearchParams();

  const genre = document.getElementById("filter-genre").value;
  const language = document.getElementById("filter-language").value;
  const yearStart = document.getElementById("filter-year-start").value;
  const yearEnd = document.getElementById("filter-year-end").value;

  if (genre) params.set("genre", genre);
  if (language) params.set("language", language);
  if (yearStart) params.set("year_start", yearStart);
  if (yearEnd) params.set("year_end", yearEnd);

  return params;
}

// ── Fetch recommendations ────────────────────────────────────

async function fetchRecommendations() {
  const params = buildParams();

  showStatus(`
    <div class="status-loading">
      <div class="spinner"></div>
      Finding the best movies for you...
    </div>
  `);
  btnRecommend.disabled = true;

  try {
    const url = `${API_BASE}/recommend?${params.toString()}`;
    const resp = await fetch(url);

    if (!resp.ok) {
      throw new Error(`Server error: ${resp.status}`);
    }

    const data = await resp.json();
    clearStatus();
    renderResults(data.results, data.total_filtered);
  } catch (err) {
    console.error("Fetch error:", err);
    showStatus(`<p style="color:#ff4757;">⚠️ Could not connect to the server. Make sure the backend is running.</p>`);
    resultsSection.innerHTML = "";
  } finally {
    btnRecommend.disabled = false;
  }
}

// ── Surprise Me ──────────────────────────────────────────────

async function fetchSurprise() {
  showStatus(`
    <div class="status-loading">
      <div class="spinner"></div>
      🎲 Rolling the dice for you...
    </div>
  `);
  btnSurprise.disabled = true;

  try {
    const resp = await fetch(`${API_BASE}/surprise`);

    if (!resp.ok) {
      throw new Error(`Server error: ${resp.status}`);
    }

    const data = await resp.json();
    clearStatus();
    renderResults(data.results, 1);
  } catch (err) {
    console.error("Surprise error:", err);
    showStatus(`<p style="color:#ff4757;">⚠️ Could not reach the server.</p>`);
  } finally {
    btnSurprise.disabled = false;
  }
}

// ── Event Listeners ──────────────────────────────────────────

btnRecommend.addEventListener("click", fetchRecommendations);
btnSurprise.addEventListener("click", fetchSurprise);

// Allow hitting Enter inside year inputs to trigger search
document.querySelectorAll("input[type='number']").forEach(el => {
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter") fetchRecommendations();
  });
});

// ── Init ─────────────────────────────────────────────────────

populateFilters();
showWelcome();
