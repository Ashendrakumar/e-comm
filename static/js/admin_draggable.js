document.addEventListener('DOMContentLoaded', function() {
  const tableBody = document.querySelector('tbody');
  if (!tableBody) return;

  // Load Sortable.js from CDN
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js';
  script.onload = initSortable;
  document.head.appendChild(script);
});

function initSortable() {
  const tableBody = document.querySelector('tbody');
  if (!tableBody) return;

  // Enable sorting on tbody
  Sortable.create(tableBody, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    dragClass: 'sortable-drag',
    handle: '.order-handle',
    onEnd: function(evt) {
      const rows = Array.from(tableBody.querySelectorAll('tr'));
      const orderInputs = rows.map(row => ({
        id: row.dataset.id || extractIdFromRow(row),
        orderField: row.querySelector('[name*="order"]'),
      }));

      // Update order fields and prepare for submission
      orderInputs.forEach((item, index) => {
        if (item.orderField) {
          item.orderField.value = index;
        }
      });

      // Send AJAX request to reorder
      const urlPath = window.location.pathname;
      const isSection = urlPath.includes('homepagesection');
      const isBanner = urlPath.includes('homepagebanner');

      if (isSection || isBanner) {
        const ids = orderInputs.map(item => item.id);
        const endpoint = isSection
          ? '/pages/api/homepage/sections/reorder/'
          : '/pages/api/homepage/banners/reorder/';
        const dataKey = isSection ? 'section_ids' : 'banner_ids';

        fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          body: JSON.stringify({
            [dataKey]: ids,
          }),
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            showToast('Order saved successfully', 'success');
          } else {
            showToast('Error saving order: ' + data.error, 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          showToast('Error saving order', 'error');
        });
      }
    },
  });

  // Add CSS for better visual feedback
  const style = document.createElement('style');
  style.textContent = `
    .sortable-ghost {
      opacity: 0.5;
      background-color: #f5f5f5;
    }
    .sortable-drag {
      opacity: 1;
      background-color: #e8f4f8;
      cursor: grabbing;
    }
    tbody tr {
      cursor: grab;
    }
    tbody tr:active {
      cursor: grabbing;
    }
  `;
  document.head.appendChild(style);
}

function extractIdFromRow(row) {
  // Try to extract ID from various possible locations
  const idInput = row.querySelector('[name*="id"]');
  if (idInput) return idInput.value;

  const editLink = row.querySelector('a[href*="/change/"]');
  if (editLink) {
    const match = editLink.href.match(/\/(\d+)\/change\//);
    return match ? match[1] : null;
  }

  return row.dataset.id || null;
}

function getCsrfToken() {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    background-color: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
    color: white;
    border-radius: 4px;
    z-index: 9999;
    font-size: 14px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
