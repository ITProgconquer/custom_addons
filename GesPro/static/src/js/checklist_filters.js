odoo.define('gespro.checklist_filters', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderBody: function () {
            var $result = this._super.apply(this, arguments);
            
            // Ajouter les écouteurs après rendu
            this.$el.on('click', '.filter-btn', function (ev) {
                var $btn = $(ev.currentTarget);
                var category = $btn.data('category');
                
                // Activer le bouton
                $btn.siblings().removeClass('active');
                $btn.addClass('active');
                
                // Filtrer les lignes
                var $rows = $btn.closest('.o_list_view').find('tbody tr');
                $rows.each(function () {
                    var $row = $(this);
                    if (category === 'all') {
                        $row.show();
                    } else {
                        var badge = $row.find('.badge').text().toLowerCase();
                        if (badge.includes(category)) {
                            $row.show();
                        } else {
                            $row.hide();
                        }
                    }
                });
            });
            
            return $result;
        },
    });
});