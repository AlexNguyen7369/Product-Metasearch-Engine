// Vanilla JS, no build step, calls the FastAPI backend directly.

const form = document.getElementById("search-form");
const input = document.getElementById("search-input");
const status = document.getElementById("status");
const results = document.getElementById("results");
const testPageButton = document.getElementById("test-page-button");

// Marketplace-feature scaffold — filters/sort/pagination.
// price_min/price_max/sort are wired to /api/search (see search_service.py).
// category is still a no-op: SerpAPI's normalized results don't carry a
// category field, so there's nothing on the backend to filter by yet
// (the <select> is disabled below for that reason). Pagination is also
// still unwired — /api/search returns one unpaginated batch of results.
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

testPageButton.addEventListener("click", () => {
  window.location.href = "/test";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  await runSearch(query);
});

applyFiltersButton.addEventListener("click", () => {
  const query = input.value.trim();
  if (!query) {
    status.textContent = "Enter a search query first — Apply re-runs it with the current filters/sort.";
    return;
  }
  runSearch(query);
});

async function runSearch(query) {
  status.textContent = "Searching...";
  results.innerHTML = "";

  const params = new URLSearchParams({ q: query, sort: sortSelect.value });
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
