/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CeoDashboard extends Component {
    static template = "gespro.CeoDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            urgent_count: 0,
            pending: [],
            status_data: [],
            monthly_data: [],
        });

        onWillStart(async () => {
            const data = await this.orm.call("gespro.appel", "get_ceo_dashboard_data", []);
            Object.assign(this.state, data);
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    renderCharts() {
        const ctx1 = document.getElementById("statusChart");
        if (ctx1) {
            new Chart(ctx1, {
                type: "pie",
                data: {
                    labels: this.state.status_data.map(d => d.state),
                    datasets: [{
                        data: this.state.status_data.map(d => d.state_count),
                        backgroundColor: ["#2e7d32", "#e65100", "#0277bd", "#c62828", "#9e9e9e"],
                    }]
                }
            });
        }

        const ctx2 = document.getElementById("monthChart");
        if (ctx2) {
            new Chart(ctx2, {
                type: "bar",
                data: {
                    labels: this.state.monthly_data.map(d => d.date_publication),
                    datasets: [{
                        label: "Appels",
                        data: this.state.monthly_data.map(d => d.id_count),
                        backgroundColor: "#c62828",
                        borderRadius: 8,
                    }]
                }
            });
        }
    }
}

registry.category("actions").add("gespro_ceo_dashboard", CeoDashboard);