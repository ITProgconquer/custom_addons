/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        this.events = {
            ...this.events,
            "click .filter-btn": this._onFilterClick,
        };
    },

    _onFilterClick(ev) {
        const btn = ev.currentTarget;
        const category = btn.dataset.category;

        // Activer le bouton
        btn.closest(".d-flex").querySelectorAll(".filter-btn").forEach(b => {
            b.classList.remove("active");
        });
        btn.classList.add("active");

        // Filtrer les lignes
        const rows = this.el.querySelectorAll("tbody tr.o_data_row");
        rows.forEach(row => {
            if (category === "all") {
                row.style.display = "";
            } else {
                const badge = row.querySelector(".badge");
                if (badge) {
                    const text = badge.textContent.toLowerCase();
                    row.style.display = text.includes(category) ? "" : "none";
                }
            }
        });
    },
});