// table-filter-sort.js
(function () {
  function filterTable(table, input) {
    if (!table || !input) return;

    input.addEventListener("input", () => {
      const term = input.value.toLowerCase();
      const rows = table.querySelectorAll("tbody tr");
      rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
      });
    });
  }

  function sortTable(table) {
    if (!table) return;

    const headers = table.querySelectorAll("thead th");
    headers.forEach((header, index) => {
      header.style.cursor = "pointer";

      header.addEventListener("click", () => {
        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr"));
        const asc = header.dataset.sortOrder !== "asc";

        // reset arrows
        headers.forEach(h => {
          h.textContent = h.textContent.replace(/[\u25B2\u25BC]/g, "").trim();
          delete h.dataset.sortOrder;
        });

        // set arrow
        header.dataset.sortOrder = asc ? "asc" : "desc";
        header.textContent += asc ? " ▲" : " ▼";

        // sort rows
        rows.sort((a, b) => {
          const ta = a.children[index].textContent.trim();
          const tb = b.children[index].textContent.trim();
          const na = parseFloat(ta);
          const nb = parseFloat(tb);

          if (!isNaN(na) && !isNaN(nb)) return asc ? na - nb : nb - na;
          return asc ? ta.localeCompare(tb) : tb.localeCompare(ta);
        });

        rows.forEach(r => tbody.appendChild(r));
      });
    });
  }

  /**
   * Initialize a table with sorting & filtering
   * @param {HTMLElement} table - the table element
   * @param {string} inputId - ID of the input element
   */
  function initTable(table, inputId) {
    const input = document.getElementById(inputId);
    if (!table || !input) {
      console.warn("Table or input not found", table, inputId);
      return;
    }

    filterTable(table, input);
    sortTable(table);
  }

  // expose globally
  window.initTable = initTable;
})();
