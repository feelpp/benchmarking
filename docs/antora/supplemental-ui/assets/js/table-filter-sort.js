
document.addEventListener("DOMContentLoaded", function() {
  // --- Filter input ---
  const input = document.getElementById('filterInput');
  const table = document.querySelector('.scrollable table');
  if (input && table) {
    input.addEventListener('input', function() {
      const term = input.value.toLowerCase();
      for (const row of table.querySelectorAll('tbody tr')) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      }
    });
  }

  // --- Table sorting ---
  if (table) {
    const headers = table.querySelectorAll('thead th');

    headers.forEach((header, index) => {
      header.style.cursor = 'pointer';
      header.addEventListener('click', () => {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const asc = header.dataset.sortOrder !== 'asc';

        // Reset all headers' arrows
        headers.forEach(h => {
          h.textContent = h.textContent.replace(/[\u25B2\u25BC]\s*$/, '').trim();
          delete h.dataset.sortOrder;
        });

        // Set current header arrow
        header.dataset.sortOrder = asc ? 'asc' : 'desc';
        header.textContent = header.textContent.trim() + (asc ? ' ▲' : ' ▼');

        // Sort rows
        rows.sort((a, b) => {
          const ta = a.children[index]?.textContent.trim();
          const tb = b.children[index]?.textContent.trim();
          const na = parseFloat(ta), nb = parseFloat(tb);
          if (!isNaN(na) && !isNaN(nb)) {
            return asc ? na - nb : nb - na;
          }
          return asc ? ta.localeCompare(tb) : tb.localeCompare(ta);
        });

        // Reinsert sorted rows
        rows.forEach(row => tbody.appendChild(row));
      });
    });
  }
});