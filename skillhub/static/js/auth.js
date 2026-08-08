/**
 * SkillHub Auth - Login/logout/token management
 */
const Auth = {
    TOKEN_KEY: 'skillhub_token',
    USER_KEY: 'skillhub_user',

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    },

    isLoggedIn() {
        return !!this.getToken();
    },

    getUser() {
        const data = localStorage.getItem(this.USER_KEY);
        return data ? JSON.parse(data) : null;
    },

    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    async login(username, password) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        this.setToken(data.access_token);

        // Decode JWT payload to get user info
        try {
            const payload = JSON.parse(atob(data.access_token.split('.')[1]));
            this.setUser({ id: payload.user_id, role: payload.role });
        } catch (e) {
            // Token decode failed, user info unavailable
        }

        return data;
    },

    logout() {
        // Call server to clear the auth cookie
        fetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
        this.clearToken();
    },

    getRole() {
        const user = this.getUser();
        return user ? user.role : null;
    },

    isAdmin() {
        return this.getRole() === 'admin';
    }
};
