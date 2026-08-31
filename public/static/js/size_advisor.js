// AI Size Advisor Modal & Recommendation Engine Client

document.addEventListener('DOMContentLoaded', () => {
  initSizeAdvisor();
});

function initSizeAdvisor() {
  const form = document.getElementById('sizeAdvisorForm');
  if (form) {
    form.addEventListener('submit', handleSizeAdvisorSubmit);
  }

  // If user is on product detail page, check for quick size recommendation
  const productEl = document.getElementById('productDetailContainer');
  if (productEl) {
    const productId = productEl.dataset.productId;
    checkQuickSizeAdvice(productId);
  }
}

async function checkQuickSizeAdvice(productId) {
  const user = getCurrentUser();
  if (!user) return;

  try {
    const data = await apiFetch(`/size-advisor/quick-check/${productId}`);
    if (data.has_measurements && data.recommendation) {
      const banner = document.getElementById('quickSizeAdviceBanner');
      if (banner) {
        banner.innerHTML = `
          <div class="d-flex align-items-center justify-content-between p-3 rounded bg-light border border-indigo mb-3">
            <div class="d-flex align-items-center gap-3">
              <div class="rounded-circle bg-dark text-white p-2 d-flex align-items-center justify-content-center" style="width: 38px; height: 38px;">
                <i class="bi bi-stars text-warning"></i>
              </div>
              <div>
                <div class="fw-bold text-dark small">AI Fit Recommendation: <span class="badge bg-dark fs-6">${data.recommendation.recommended_size}</span> (${data.recommendation.confidence_score}% Fit Confidence)</div>
                <div class="text-muted" style="font-size: 0.78rem;">${data.recommendation.commentary}</div>
              </div>
            </div>
            <button class="btn btn-sm btn-dark rounded-pill px-3" onclick="selectRecommendedSize('${data.recommendation.recommended_size}')">Select Size</button>
          </div>
        `;
        banner.classList.remove('d-none');
      }
    }
  } catch (e) {
    // ignore
  }
}

async function handleSizeAdvisorSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById('btnCalculateSize');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Analyzing Biometrics...`;

  const gender = document.querySelector('input[name="advisorGender"]:checked')?.value || 'unisex';
  const height_cm = parseFloat(document.getElementById('advisorHeight')?.value) || null;
  const weight_kg = parseFloat(document.getElementById('advisorWeight')?.value) || null;
  const chest_cm = parseFloat(document.getElementById('advisorChest')?.value) || null;
  const waist_cm = parseFloat(document.getElementById('advisorWaist')?.value) || null;
  const hips_cm = parseFloat(document.getElementById('advisorHips')?.value) || null;
  const preferred_fit = document.getElementById('advisorFitPref')?.value || 'regular';
  const save_to_profile = document.getElementById('advisorSaveProfile')?.checked || false;

  const productEl = document.getElementById('productDetailContainer');
  const productId = productEl ? parseInt(productEl.dataset.productId) : null;
  const categoryName = productEl ? productEl.dataset.categoryName : 'Tops';

  try {
    const payload = {
      product_id: productId,
      category_name: categoryName,
      gender,
      height_cm,
      weight_kg,
      chest_cm,
      waist_cm,
      hips_cm,
      preferred_fit,
      save_to_profile
    };

    const res = await apiFetch('/size-advisor/recommend', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    renderSizeAdvisorResult(res);
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

function renderSizeAdvisorResult(data) {
  const resultContainer = document.getElementById('sizeAdvisorResults');
  if (!resultContainer) return;

  resultContainer.innerHTML = `
    <div class="card border-0 bg-light p-4 rounded-3 text-center mb-3">
      <div class="text-uppercase tracking-wider text-muted small fw-bold mb-1">Optimal AI Fit Recommendation</div>
      <div class="display-4 fw-bold text-dark mb-2">${data.recommended_size}</div>
      <div class="d-inline-flex align-items-center justify-content-center gap-2 mb-3">
        <span class="badge bg-success px-3 py-2 rounded-pill"><i class="bi bi-shield-check me-1"></i>${data.confidence_score}% Fit Confidence</span>
        <span class="badge bg-secondary px-3 py-2 rounded-pill">${data.fit_preference} Fit Profile</span>
      </div>
      <p class="text-secondary small mb-3">${data.commentary}</p>

      ${data.secondary_size ? `
        <div class="alert alert-light border small text-start py-2 px-3 mb-3">
          <strong>Alternative:</strong> ${data.secondary_reason}
        </div>
      ` : ''}

      <div class="d-flex justify-content-center gap-2">
        <button class="btn btn-dark rounded-pill px-4" onclick="selectRecommendedSize('${data.recommended_size}')">
          <i class="bi bi-check-lg me-1"></i> Apply Size ${data.recommended_size}
        </button>
      </div>
    </div>
  `;
  resultContainer.classList.remove('d-none');
}

function selectRecommendedSize(size) {
  // Find size button on product page
  const sizeBtns = document.querySelectorAll('.size-picker-btn');
  let matched = false;
  sizeBtns.forEach(btn => {
    if (btn.dataset.size === size && !btn.classList.contains('disabled')) {
      btn.click();
      matched = true;
    }
  });

  // Close modal if open
  const modalEl = document.getElementById('sizeAdvisorModal');
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
  }

  if (matched) {
    showToast(`Size ${size} applied based on AI recommendations!`, 'success');
  } else {
    showToast(`Recommended size is ${size} (check availability for this product)`, 'info');
  }
}
