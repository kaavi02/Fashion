// Shopping Cart Client Logic

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('cartPageContainer')) {
    loadCartPage();
  }
});

// Helper to get and set local cart cache
function getLocalCartCache() {
  try {
    const raw = localStorage.getItem('vogue_cart_cache');
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function setLocalCartCache(items) {
  try {
    localStorage.setItem('vogue_cart_cache', JSON.stringify(items));
  } catch (e) {}
}

async function loadCartPage() {
  const container = document.getElementById('cartItemsList');
  const summaryContainer = document.getElementById('cartSummaryContainer');
  if (!container) return;

  try {
    const sid = getSessionId();
    let data = await apiFetch(`/cart?session_id=${sid}`);

    // If serverless container recycled and cart is empty, but local cache exists, auto-sync
    const localCache = getLocalCartCache();
    if ((!data.items || data.items.length === 0) && localCache.length > 0) {
      for (const item of localCache) {
        try {
          await apiFetch('/cart/add', {
            method: 'POST',
            body: JSON.stringify({ variant_id: item.variant_id, quantity: item.quantity, session_id: sid })
          });
        } catch (syncErr) {
          console.warn("Cart auto-sync item skipped:", syncErr);
        }
      }
      // Re-fetch after syncing
      data = await apiFetch(`/cart?session_id=${sid}`);
    }

    if (!data.items || data.items.length === 0) {
      setLocalCartCache([]);
      container.innerHTML = `
        <div class="text-center py-5">
          <div class="mb-3 text-muted" style="font-size: 3rem;"><i class="bi bi-bag-x"></i></div>
          <h4 class="fw-bold">Your shopping bag is empty</h4>
          <p class="text-muted">Explore our new season arrivals and find your perfect fit.</p>
          <a href="/products" class="btn btn-dark rounded-pill px-4 py-2 mt-2">Shop The Collection</a>
        </div>
      `;
      if (summaryContainer) summaryContainer.style.display = 'none';
      return;
    }

    // Save active items to local cache for resilience
    setLocalCartCache(data.items.map(i => ({ variant_id: i.variant_id, quantity: i.quantity })));

    if (summaryContainer) summaryContainer.style.display = 'block';

    let html = `
      <table class="table cart-table align-middle">
        <thead>
          <tr>
            <th>Product</th>
            <th>Size & Color</th>
            <th>Unit Price</th>
            <th>Quantity</th>
            <th>Subtotal</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
    `;

    data.items.forEach(item => {
      html += `
        <tr>
          <td>
            <div class="d-flex align-items-center gap-3">
              <img src="${item.image_url}" class="rounded" style="width: 60px; height: 75px; object-fit: cover;" alt="${item.product_name}">
              <div>
                <a href="/product/${item.product_slug}" class="fw-semibold text-dark text-decoration-none d-block">${item.product_name}</a>
                <span class="text-muted small">SKU: #${item.variant_id}</span>
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-light text-dark border">${item.size}</span>
              <span class="color-dot" style="background-color: ${item.color_hex};" title="${item.color_name}"></span>
              <span class="small text-muted">${item.color_name}</span>
            </div>
          </td>
          <td class="fw-semibold">₹${item.price.toLocaleString()}</td>
          <td>
            <div class="qty-control">
              <button class="qty-btn" onclick="updateCartQty(${item.id}, ${item.quantity - 1})">-</button>
              <input type="text" class="qty-input" value="${item.quantity}" readonly>
              <button class="qty-btn" onclick="updateCartQty(${item.id}, ${item.quantity + 1})">+</button>
            </div>
          </td>
          <td class="fw-bold">₹${item.item_total.toLocaleString()}</td>
          <td>
            <button class="btn btn-sm btn-link text-danger p-0" onclick="removeCartItem(${item.id})">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;

    // Render Order Summary
    document.getElementById('summarySubtotal').textContent = `₹${data.subtotal.toLocaleString()}`;
    document.getElementById('summaryShipping').textContent = data.shipping === 0 ? 'FREE' : `₹${data.shipping.toLocaleString()}`;
    document.getElementById('summaryTotal').textContent = `₹${data.total.toLocaleString()}`;
    
    const countEl = document.getElementById('cartItemsCount');
    if (countEl) countEl.textContent = `(${data.total_count} items)`;

    updateCartBadge();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function updateCartQty(itemId, newQty) {
  try {
    const sid = getSessionId();
    await apiFetch(`/cart/${itemId}?session_id=${sid}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity: newQty })
    });
    loadCartPage();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function removeCartItem(itemId) {
  try {
    const sid = getSessionId();
    await apiFetch(`/cart/${itemId}?session_id=${sid}`, { method: 'DELETE' });
    showToast('Item removed from cart', 'info');
    loadCartPage();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function handleAddToCart(variantId, quantity = 1) {
  try {
    const sid = getSessionId();
    const res = await apiFetch('/cart/add', {
      method: 'POST',
      body: JSON.stringify({ variant_id: variantId, quantity, session_id: sid })
    });
    
    // Save to local cache
    const cache = getLocalCartCache();
    const existing = cache.find(i => i.variant_id === variantId);
    if (existing) {
      existing.quantity += quantity;
    } else {
      cache.push({ variant_id: variantId, quantity });
    }
    setLocalCartCache(cache);

    showToast('Added to your shopping bag!', 'success');
    updateCartBadge();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}
