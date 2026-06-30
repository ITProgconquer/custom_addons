/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

const IDLE_TIMEOUT = 120; // secondes avant verrouillage

class SessionLockOverlay extends Component {
    static template = "GesPro.SessionLockOverlay";
    setup() {
        this.orm = useService("orm");
        this.user = useService("user");
        this.state = useState({
            locked: false,
            password: "",
            error: "",
        });
        this.idleTimer = null;
        this.activityEvents = ["mousemove", "keydown", "click", "scroll", "touchstart"];
        this.resetTimer = this.resetTimer.bind(this);
        this.onActivity = this.onActivity.bind(this);
        onMounted(() => {
            this.startTimer();
            this.activityEvents.forEach((ev) => document.addEventListener(ev, this.onActivity));
        });
        onWillUnmount(() => {
            this.clearTimer();
            this.activityEvents.forEach((ev) => document.removeEventListener(ev, this.onActivity));
        });
    }

    startTimer() {
        this.clearTimer();
        this.idleTimer = setTimeout(() => {
            if (!this.state.locked) {
                this.state.locked = true;
            }
        }, IDLE_TIMEOUT * 1000);
    }

    clearTimer() {
        if (this.idleTimer) {
            clearTimeout(this.idleTimer);
            this.idleTimer = null;
        }
    }

    resetTimer() {
        if (!this.state.locked) {
            this.startTimer();
        }
    }

    onActivity() {
        if (!this.state.locked) {
            this.startTimer();
        }
    }

    async unlock() {
        try {
            await this.orm.call("res.users", "check_credentials", [this.user.userId, this.state.password]);
            this.state.locked = false;
            this.state.password = "";
            this.state.error = "";
            this.startTimer();
        } catch {
            this.state.error = "Mot de passe incorrect.";
        }
    }

    logout() {
        window.location = "/web/session/logout";
    }
}

registry.category("main_components").add("SessionLockOverlay", {
    Component: SessionLockOverlay,
});