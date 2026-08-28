// Vanilla JS, no build step, calls the FastAPI backend directly.

const form = document.getElementById("search-form");
const input = document.getElementById("search-input");
const status = document.getElementById("status");
const results = document.getElementById("results");
const testPageButton = document.getElementById("test-page-button");

// Marketplace-feature scaffold — filters/sort/pagination.
// price_min/price_max/sort/page are all wired to /api/search (see
// search_service.py). category is still a no-op: SerpAPI's normalized
// results don't carry a category field, so there's nothing on the
// backend to filter by yet (the <select> is disabled below for that
// reason).
const categorySelect = document.getElementById("filter-category");
const priceMinInput = document.getElementById("filter-price-min");
const priceMaxInput = document.getElementById("filter-price-max");
const sortSelect = document.getElementById("sort-select");
const applyFiltersButton = document.getElementById("apply-filters");
const prevPageButton = document.getElementById("prev-page");
const nextPageButton = document.getElementById("next-page");
const pageIndicator = document.getElementById("page-indicator");

categorySelect.disabled = true;
categorySelect.title = "Not wired to the API yet — results have no category data";

let lastResults = null; // last successful search response
let currentQuery = ""; // query behind the currently displayed page, for Prev/Next

testPageButton.addEventListener("click", () => {
  window.location.href = "/test";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  await runSearch(query, 1);
});

applyFiltersButton.addEventListener("click", () => {
  const query = input.value.trim();
  if (!query) {
    status.textContent = "Enter a search query first — Apply re-runs it with the current filters/sort.";
    return;
  }
  runSearch(query, 1); // a new filter/sort combination starts back at page 1
});

prevPageButton.addEventListener("click", () => {
  if (lastResults && lastResults.page > 1) {
    runSearch(currentQuery, lastResults.page - 1);
  }
});

nextPageButton.addEventListener("click", () => {
  if (lastResults) {
    runSearch(currentQuery, lastResults.page + 1);
  }
});

async function runSearch(query, page) {
  currentQuery = query;
  status.textContent = "Searching...";
  results.innerHTML = "";

  const params = new URLSearchParams({ q: query, sort: sortSelect.value, page: String(page) });
  if (priceMinInput.value) params.set("price_min", priceMinInput.value);
  if (priceMaxInput.value) params.set("price_max", priceMaxInput.value);

  try {
    const response = await fetch(`/api/search?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const data = await response.json();
    renderResults(data);
  } catch (err) {
    status.textContent = `Error: ${err.message}`;
  }
}

function renderResults(data) {
  lastResults = data;
  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
  pageIndicator.textContent = `Page ${data.page} of ${totalPages}`;
  prevPageButton.disabled = data.page <= 1;
  nextPageButton.disabled = data.page >= totalPages;

  status.textContent = `${data.total} result(s)${data.cached ? " (cached)" : ""}`;

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
