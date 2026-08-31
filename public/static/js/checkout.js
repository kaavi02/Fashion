// Checkout Process & Order Submission

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('checkoutForm')) {
    initCheckoutPage();
  }
});

async function initCheckoutPage() {
  // Pre-fill user data if authenticated
  const user = getCurrentUser();
  if (user) {
    document.getElementById('checkoutName').value = user.full_name || '';
    document.getElementById('checkoutEmail').value = user.email || '';
    document.getElementById('checkoutPhone').value = user.phone || '';
    document.getElementById('checkoutAddress').value = user.address || '';
    document.getElementById('checkoutCity').value = user.city || '';
    document.getElementById('checkoutState').value = user.state || '';
    document.getElementById('checkoutPostal').value = user.postal_code || '';
  }

  // Load Cart Preview
  try {
    const sid = getSessionId();
    const data = await apiFetch(`/cart?session_id=${sid}`);
    if (!data.items || data.items.length === 0) {
      window.location.href = '/cart';
      return;
    }

    const previewList = document.getElementById('checkoutOrderItems');
    if (previewList) {
      previewList.innerHTML = data.items.map(item => `
        <div class="d-flex align-items-center justify-content-between py-2 border-bottom">
          <div class="d-flex align-items-center gap-2">
            <img src="${item.image_url}" class="rounded" style="width: 40px; height: 50px; object-fit: cover;">
            <div>
              <div class="fw-semibold small text-truncate" style="max-width: 180px;">${item.product_name}</div>
              <div class="text-muted" style="font-size: 0.75rem;">Size: ${item.size} | Qty: ${item.quantity}</div>
            </div>
          </div>
          <div class="fw-bold small">₹${item.item_total.toLocaleString()}</div>
        </div>
      `).join('');
    }

    document.getElementById('checkoutSubtotal').textContent = `₹${data.subtotal.toLocaleString()}`;
    document.getElementById('checkoutShipping').textContent = data.shipping === 0 ? 'FREE' : `₹${data.shipping.toLocaleString()}`;
    document.getElementById('checkoutTotal').textContent = `₹${data.total.toLocaleString()}`;
  } catch (err) {
    showToast(err.message, 'danger');
  }

  // Form submission
  document.getElementById('checkoutForm').addEventListener('submit', handleCheckoutSubmit);
}

async function handleCheckoutSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById('btnPlaceOrder');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Authorizing & Placing Order...`;

  const paymentMethodEl = document.querySelector('input[name="paymentMethod"]:checked');
  const payment_method = paymentMethodEl ? paymentMethodEl.value : 'Credit/Debit Card';

  const payload = {
    shipping_name: document.getElementById('checkoutName').value,
    shipping_email: document.getElementById('checkoutEmail').value,
    shipping_phone: document.getElementById('checkoutPhone').value,
    shipping_address: document.getElementById('checkoutAddress').value,
    shipping_city: document.getElementById('checkoutCity').value,
    shipping_state: document.getElementById('checkoutState').value,
    shipping_postal_code: document.getElementById('checkoutPostal').value,
    shipping_country: 'India',
    payment_method: payment_method,
    session_id: getSessionId()
  };

  try {
    const order = await apiFetch('/checkout/process', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    showToast('Order confirmed successfully!', 'success');
    updateCartBadge();
    
    // Redirect to orders page or display confirmation
    setTimeout(() => {
      window.location.href = `/orders`;
    }, 1200);
  } catch (err) {
    showToast(err.message, 'danger');
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}
