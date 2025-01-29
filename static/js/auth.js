class Auth {
    static token = null;
    static tokenExpiryTimer = null;
    static tokenWarningTimer = null;

    static async login(username, password, code = null) {
        try {
            const data = await Api.login(username, password, code);
            if (data.token) {
                this.token = data.token;
                this.setupTokenExpiry(data.expiry_time);
                return { success: true };
            }
            return { success: false };
        } catch (error) {
            if (error.status === 403) {
                return { needsTwoFactor: true };
            }
            throw error;
        }
    }

    static setupTokenExpiry(expiryTime) {
        this.clearTimers();
        
        const warningTime = (expiryTime - 5) * 1000;
        if (warningTime > 0) {
            this.tokenWarningTimer = setTimeout(() => {
                if (this.isAuthenticated()) {
                    UI.showFeedback('Sua sessão irá expirar em 5 segundos!');
                }
            }, warningTime);
        }

        this.tokenExpiryTimer = setTimeout(() => {
            if (this.isAuthenticated()) {
                window.location.reload();
            }
        }, expiryTime * 1000);
    }

    static clearTimers() {
        if (this.tokenExpiryTimer) {
            clearTimeout(this.tokenExpiryTimer);
            this.tokenExpiryTimer = null;
        }
        if (this.tokenWarningTimer) {
            clearTimeout(this.tokenWarningTimer);
            this.tokenWarningTimer = null;
        }
    }

    static logout() {
        this.clearTimers();
        this.token = null;
        UI.showLoginPage();
    }

    static silentLogout() {
        this.clearTimers();
        this.token = null;
        UI.showLoginPage();
    }

    static isAuthenticated() {
        return this.token !== null;
    }

    static handleUnauthorized() {
        UI.showFeedback('Sessão expirada. Por favor, faça login novamente.');
        this.logout();
    }
}
