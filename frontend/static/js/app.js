// Vanilla JS, no build step, calls the FastAPI backend directly.

const form = document.getElementById("search-form");
const input = document.getElementById("search-input");
const status = document.getElementById("status");
const results = document.getElementById("results");
const testPageButton = document.getElementById("test-page-button");

// Marketplace-feature scaffold — filters/sort/pagination. None of this
// talks to the backend yet: /api/search takes only `q`. These exist so
// the UI has something to wire real params into once the API supports
// them, instead of building the controls and the API logic in lockstep.
const categorySelect = document.getElementById("filter-category");
const priceMinInput = document.getElementById("filter-price-min");
const priceMaxInput = document.getElementById("filter-price-max");
const sortSelect = document.getElementById("sort-select");
const applyFiltersButton = document.getElementById("apply-filters");
const prevPageButton = document.getElementById("prev-page");
const nextPageButton = document.getElementById("next-page");
const pageIndicator = document.getElementById("page-indicator");

let lastResults = null; // last successful search response, for future client-side testing

testPageButton.addEventListener("click", () => {
  window.location.href = "/test";
});

applyFiltersButton.addEventListener("click", () => {
  const filters = {
    category: categorySelect.value || null,
    priceMin: priceMinInput.value ? Number(priceMinInput.value) : null,
    priceMax: priceMaxInput.value ? Number(priceMaxInput.value) : null,
    sort: sortSelect.value,
  };
  console.log("Filters selected (stub — not sent to backend yet):", filters);
  status.textContent = lastResults
    ? "Filters/sort are captured but not applied yet — /api/search has no filter params."
    : "Run a search first, then filters can be tested against the results.";
});

// Pagination buttons stay disabled — /api/search returns one unpaginated
// batch of results, so there's nothing to page through yet.

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;

  status.textContent = "Searching...";
  results.innerHTML = "";

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const data = await response.json();
    renderResults(data);
  } catch (err) {
    status.textContent = `Error: ${err.message}`;
  }
});

function renderResults(data) {
  lastResults = data;
  status.textContent = `${data.results.length} result(s)${data.cached ? " (cached)" : ""}`;

  results.innerHTML = data.results
    .map((product) => `
      <div class="product-card">
        ${product.thumbnail ? `<img src="${product.thumbnail}" alt="${product.title}" />` : ""}
        <h3>${product.title}</h3>
        <p class="price">${product.currency} ${product.price.toFixed(2)}</p>
        <p class="source">${product.source}</p>
        ${product.rating ? `<p class="rating">${product.rating} ★ (${product.review_count ?? 0} reviews)</p>` : ""}
        ${product.stock ? `<p class="stock">${product.stock}</p>` : ""}
        <a href="${product.link}" target="_blank" rel="noopener">View listing</a>
      </div>
    `)
    .join("");
}
