// Main application logic & navigation state
document.addEventListener('DOMContentLoaded', () => {
  updateNavUser();
  updateCartBadge();
  updateWishlistBadge();
});

function updateNavUser() {
  const user = getCurrentUser();
  const userNavContainer = document.getElementById('userNavContainer');
  if (!userNavContainer) return;

  if (user) {
    const adminBadge = user.is_admin ? `
      <a href="/admin" class="btn btn-warning text-dark rounded-pill px-3 py-2 fw-bold d-inline-flex align-items-center gap-1 me-2 shadow-sm" style="font-size: 0.8rem; letter-spacing: 0.05em;">
        <i class="bi bi-shield-lock-fill"></i> Admin Console
      </a>
    ` : '';

    const adminDropdownItem = user.is_admin ? `
      <li><a class="dropdown-item fw-bold text-warning" href="/admin"><i class="bi bi-speedometer2 me-2"></i>Admin Studio</a></li>
      <li><hr class="dropdown-divider"></li>
    ` : '';

    userNavContainer.innerHTML = `
      <div class="d-flex align-items-center">
        ${adminBadge}
        <div class="dropdown">
          <button class="btn btn-outline-light rounded-pill px-3 py-2 dropdown-toggle d-flex align-items-center gap-2" type="button" data-bs-toggle="dropdown" style="font-size: 0.82rem;">
            <i class="bi bi-person-circle"></i>
            <span>${user.full_name.split(' ')[0]}</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-end shadow-sm">
            <li><h6 class="dropdown-header">${user.email}</h6></li>
            ${adminDropdownItem}
            <li><a class="dropdown-item" href="/profile"><i class="bi bi-person me-2"></i>My Profile & AI Sizes</a></li>
            <li><a class="dropdown-item" href="/orders"><i class="bi bi-box-seam me-2"></i>My Orders</a></li>
            <li><a class="dropdown-item" href="/wishlist"><i class="bi bi-heart me-2"></i>Wishlist</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><button class="dropdown-item text-danger" onclick="logoutUser()"><i class="bi bi-box-arrow-right me-2"></i>Sign Out</button></li>
          </ul>
        </div>
      </div>
    `;
  } else {
    userNavContainer.innerHTML = `
      <a href="/login" class="btn btn-outline-light rounded-pill px-3 py-2 fw-semibold d-inline-flex align-items-center gap-1" style="font-size: 0.82rem;">
        <i class="bi bi-person"></i> Sign In
      </a>
    `;
  }
}

function logoutUser() {
  clearAuth();
  showToast('You have signed out', 'info');
  setTimeout(() => {
    window.location.href = '/';
  }, 500);
}

async function updateCartBadge() {
  const badge = document.getElementById('cartBadge');
  if (!badge) return;
  try {
    const sid = getSessionId();
    const data = await apiFetch(`/cart?session_id=${sid}`);
    const count = data.total_count || 0;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  } catch (err) {
    // ignore
  }
}

async function updateWishlistBadge() {
  const badge = document.getElementById('wishlistBadge');
  if (!badge) return;
  const user = getCurrentUser();
  if (!user) {
    badge.style.display = 'none';
    return;
  }
  try {
    const data = await apiFetch('/wishlist');
    const count = data.length || 0;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  } catch (err) {
    badge.style.display = 'none';
  }
}

async function toggleWishlist(productId, btnElement) {
  const user = getCurrentUser();
  if (!user) {
    showToast('Please sign in to save items to your wishlist', 'info');
    setTimeout(() => { window.location.href = '/login'; }, 1000);
    return;
  }

  try {
    const res = await apiFetch(`/wishlist/toggle/${productId}`, { method: 'POST' });
    showToast(res.message, 'success');
    if (btnElement) {
      if (res.in_wishlist) {
        btnElement.classList.add('active');
        btnElement.innerHTML = '<i class="bi bi-heart-fill text-danger"></i>';
      } else {
        btnElement.classList.remove('active');
        btnElement.innerHTML = '<i class="bi bi-heart"></i>';
      }
    }
    updateWishlistBadge();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}
