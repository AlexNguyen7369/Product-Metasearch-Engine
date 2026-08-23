// Vanilla JS, no build step, calls the FastAPI backend directly.

const form = document.getElementById("search-form");
const input = document.getElementById("search-input");
const status = document.getElementById("status");
const results = document.getElementById("results");
const testPageButton = document.getElementById("test-page-button");

testPageButton.addEventListener("click", () => {
  window.location.href = "/test";
});

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
