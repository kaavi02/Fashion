// Admin Control Studio Client Logic

document.addEventListener('DOMContentLoaded', () => {
  const user = getCurrentUser();
  if (!user || !user.is_admin) {
    showToast('Administrator privileges required. Redirecting to login...', 'danger');
    setTimeout(() => { window.location.href = '/login'; }, 1200);
    return;
  }
  loadAdminData();
});

async function loadAdminData() {
  await Promise.all([
    loadOverview(),
    loadOrders(),
    loadProducts(),
    loadUsers()
  ]);
}

async function loadOverview() {
  try {
    const data = await apiFetch('/admin/overview');
    document.getElementById('kpiRevenue').textContent = '₹' + Number(data.total_sales).toLocaleString('en-IN', { maximumFractionDigits: 0 });
    document.getElementById('kpiOrders').textContent = data.total_orders;
    document.getElementById('kpiOrdersPending').textContent = (data.status_counts['Pending'] || 0) + ' pending fulfillment';
    document.getElementById('kpiProducts').textContent = data.total_products;
    document.getElementById('kpiLowStock').textContent = data.low_stock_count;
  } catch (err) {
    console.error('Failed to load overview:', err);
    showToast(err.message, 'danger');
  }
}

async function loadOrders() {
  const tbody = document.getElementById('adminOrdersTableBody');
  const countBadge = document.getElementById('orderCountBadge');
  try {
    const orders = await apiFetch('/admin/orders');
    countBadge.textContent = `${orders.length} total orders recorded`;

    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5 text-secondary">No customer orders recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => {
      const statusBadgeClass = {
        'Pending': 'bg-secondary',
        'Confirmed': 'bg-primary',
        'Shipped': 'bg-info text-dark',
        'Delivered': 'bg-success',
        'Cancelled': 'bg-danger'
      }[o.status] || 'bg-secondary';

      const itemsSummary = o.items.map(i => `${i.product_name} (${i.size}, ${i.color_name}) x${i.quantity}`).join('<br>');

      return `
        <tr>
          <td class="fw-bold text-white">${o.order_number}</td>
          <td class="small text-secondary">${o.created_at}</td>
          <td>
            <div class="fw-semibold text-light">${o.shipping_name}</div>
            <div class="small text-secondary">${o.shipping_email} | ${o.shipping_phone}</div>
            <div class="small text-muted">${o.shipping_city}</div>
          </td>
          <td class="small text-light">${itemsSummary}</td>
          <td class="fw-bold text-warning">₹${Number(o.total_amount).toLocaleString('en-IN')}</td>
          <td>
            <span class="badge bg-dark border text-light">${o.payment_method}</span>
            <div class="small text-success">${o.payment_status}</div>
          </td>
          <td>
            <span class="badge ${statusBadgeClass}">${o.status}</span>
          </td>
          <td>
            <select class="form-select form-select-sm" onchange="updateOrderStatus(${o.id}, this.value)" style="background: #232328; color: #fff; border-color: #383842; width: 130px;">
              <option value="Pending" ${o.status === 'Pending' ? 'selected' : ''}>Pending</option>
              <option value="Confirmed" ${o.status === 'Confirmed' ? 'selected' : ''}>Confirmed</option>
              <option value="Shipped" ${o.status === 'Shipped' ? 'selected' : ''}>Shipped</option>
              <option value="Delivered" ${o.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
              <option value="Cancelled" ${o.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
            </select>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Failed to load orders:', err);
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">${err.message}</td></tr>`;
  }
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    const res = await apiFetch(`/admin/orders/${orderId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus })
    });
    showToast(res.message, 'success');
    loadOverview();
  } catch (err) {
    showToast(err.message, 'danger');
    loadOrders();
  }
}

async function loadProducts() {
  const tbody = document.getElementById('adminProductsTableBody');
  const countBadge = document.getElementById('productCountBadge');
  try {
    const products = await apiFetch('/admin/products');
    countBadge.textContent = `${products.length} products listed`;

    if (products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-secondary">No products in catalog.</td></tr>`;
      return;
    }

    tbody.innerHTML = products.map(p => {
      const variantsSummary = p.variants.map(v => `
        <div class="d-inline-flex align-items-center gap-2 p-1 me-2 mb-1 rounded" style="background: rgba(255,255,255,0.05); font-size: 0.8rem;">
          <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: ${v.color_hex}; border: 1px solid #444;"></span>
          <span>${v.size} / ${v.color_name}</span>
          <span class="badge ${v.stock_quantity <= 4 ? 'bg-danger' : 'bg-secondary'}">${v.stock_quantity} in stock</span>
          <button class="btn btn-link btn-sm p-0 text-info text-decoration-none" onclick="promptRestock(${v.id}, ${v.stock_quantity})" title="Update stock">
            <i class="bi bi-pencil-square"></i>
          </button>
        </div>
      `).join('');

      return `
        <tr>
          <td>
            <div class="d-flex align-items-center gap-3">
              <img src="${p.image_url}" alt="${p.name}" class="rounded" style="width: 48px; height: 58px; object-fit: cover;">
              <div>
                <a href="/product/${p.slug}" class="fw-bold text-white text-decoration-none d-block">${p.name}</a>
                <span class="small text-muted">ID: ${p.id}</span>
              </div>
            </div>
          </td>
          <td class="small text-light">${p.category_name}</td>
          <td class="small text-light">${p.brand_name}</td>
          <td>
            <span class="fw-bold text-white">₹${Number(p.current_price).toLocaleString('en-IN')}</span>
            ${p.base_price > p.current_price ? `<span class="small text-muted text-decoration-line-through d-block">₹${Number(p.base_price).toLocaleString('en-IN')}</span>` : ''}
          </td>
          <td>
            <div class="mb-1">${variantsSummary}</div>
            <div class="small fw-semibold text-warning">Total Inventory: ${p.total_stock}</div>
          </td>
          <td>
            ${p.is_featured ? '<span class="badge bg-warning text-dark"><i class="bi bi-star-fill me-1"></i>Featured</span>' : '<span class="text-muted small">Standard</span>'}
          </td>
          <td>
            <button class="btn btn-outline-danger btn-sm" onclick="handleDeleteProduct(${p.id}, '${p.name.replace(/'/g, "\\'")}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Failed to load products:', err);
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">${err.message}</td></tr>`;
  }
}

async function promptRestock(variantId, currentStock) {
  const input = prompt(`Enter new stock quantity for this variant (Current: ${currentStock}):`, currentStock);
  if (input === null) return;
  const newStock = parseInt(input);
  if (isNaN(newStock) || newStock < 0) {
    showToast('Invalid stock number', 'danger');
    return;
  }

  try {
    const res = await apiFetch(`/admin/variants/${variantId}/stock`, {
      method: 'PATCH',
      body: JSON.stringify({ stock: newStock })
    });
    showToast(res.message, 'success');
    loadProducts();
    loadOverview();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function handleCreateProduct(e) {
  e.preventDefault();
  const btn = document.getElementById('btnSubmitProduct');
  btn.disabled = true;
  btn.textContent = 'Publishing...';

  const payload = {
    name: document.getElementById('npName').value.trim(),
    gender: document.getElementById('npGender').value,
    category_id: parseInt(document.getElementById('npCategory').value),
    brand_id: parseInt(document.getElementById('npBrand').value),
    base_price: parseFloat(document.getElementById('npBasePrice').value),
    discount_price: document.getElementById('npDiscountPrice').value ? parseFloat(document.getElementById('npDiscountPrice').value) : null,
    image_url: document.getElementById('npImageUrl').value.trim(),
    description: document.getElementById('npDescription').value.trim(),
    size: document.getElementById('npSize').value.trim() || 'M',
    color_name: document.getElementById('npColorName').value.trim() || 'Classic Black',
    color_hex: document.getElementById('npColorHex').value || '#000000',
    stock_quantity: parseInt(document.getElementById('npStock').value) || 10
  };

  try {
    const res = await apiFetch('/admin/products', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    showToast('New product added to store catalog!', 'success');
    
    // Close modal
    const modalEl = document.getElementById('addProductModal');
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) modalInstance.hide();
    document.getElementById('newProductForm').reset();

    loadProducts();
    loadOverview();
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Save & Publish';
  }
}

async function handleDeleteProduct(productId, productName) {
  if (!confirm(`Are you sure you want to remove '${productName}' from the catalog?`)) return;

  try {
    await apiFetch(`/admin/products/${productId}`, { method: 'DELETE' });
    showToast('Product removed', 'info');
    loadProducts();
    loadOverview();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function loadUsers() {
  const tbody = document.getElementById('adminUsersTableBody');
  const countBadge = document.getElementById('userCountBadge');
  try {
    const users = await apiFetch('/admin/users');
    countBadge.textContent = `${users.length} registered accounts`;

    tbody.innerHTML = users.map(u => `
      <tr>
        <td class="text-secondary">${u.id}</td>
        <td class="fw-semibold text-white">${u.full_name}</td>
        <td>${u.email}</td>
        <td class="small text-secondary">${u.phone || '—'}</td>
        <td class="small text-secondary">${u.city || '—'}</td>
        <td>
          ${u.is_admin ? '<span class="badge bg-warning text-dark fw-bold">Admin</span>' : '<span class="badge bg-secondary">Customer</span>'}
        </td>
        <td class="small text-secondary">${u.created_at}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load users:', err);
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">${err.message}</td></tr>`;
  }
}
