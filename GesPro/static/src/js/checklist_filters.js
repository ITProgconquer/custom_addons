(function () {
    "use strict";

    document.addEventListener('click', function (ev) {
        var btn = ev.target.closest('.filter-btn');
        if (!btn) return;

        var category = btn.getAttribute('data-category');
        
        // Activer le bouton
        document.querySelectorAll('.filter-btn').forEach(function (b) {
            b.classList.remove('active');
        });
        btn.classList.add('active');
        
        // Trouver le tableau parent
        var table = btn.closest('.o_notebook_content').querySelector('.o_list_table');
        if (!table) return;
        
        var rows = table.querySelectorAll('tbody tr.o_data_row');
        rows.forEach(function (row) {
            if (category === 'all') {
                row.style.display = '';
            } else {
                var badge = row.querySelector('.badge');
                if (badge) {
                    var text = badge.textContent.toLowerCase();
                    row.style.display = text.includes(category) ? '' : 'none';
                }
            }
        });
    });
})();