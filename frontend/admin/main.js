function adminApp() {
    return {
        authenticated: false,
        loading: true,
        user: null,
        sidebarOpen: true,

        async init() {
            console.log('📌 [adminApp.init]');
            this.loading = true;

            const token = localStorage.getItem('anita_token');
            const cachedUser = localStorage.getItem('anita_user_cache');

            // if (token && cachedUser) {
            //     // No expiry check – trust the token until an API call fails
            //     console.log('🟢 Using cached user data – no server call');
            //     this.user = JSON.parse(cachedUser);
            //     this.authenticated = true;
            //     this.loading = false;
            //     return;
            // }

            // No cache – do initial validation (first load or after login)
            if (token) {
                console.log('🟡 Cache miss, validating token with server...');
                try {
                    const response = await fetch('/api/auth/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        const data = await response.json();
                        this.user = data.user;
                        this.authenticated = true;
                        // Store user for future page loads (no expiry!)
                        localStorage.setItem('anita_user_cache', JSON.stringify(data.user));
                    } else {
                        this.clearAuth();
                    }
                } catch {
                    this.clearAuth();
                }
            } else {
                this.authenticated = false;
            }
            this.loading = false;
        },

        clearAuth() {
            localStorage.removeItem('anita_token');
            localStorage.removeItem('anita_user_cache');
            this.authenticated = false;
            this.user = null;
        },

        logout() {
            this.clearAuth();
            window.location.href = '/auth/login';
        }
    };
}

// --- Global 401 handler ---
// Intercept all fetch responses and clear auth on 401
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const response = await originalFetch(...args);
    if (response.status === 401) {
        // Token expired or invalid – wipe auth
        console.warn('🔴 Received 401 – clearing auth');
        localStorage.removeItem('anita_token');
        localStorage.removeItem('anita_user_cache');
        // You may want to redirect to login
        window.location.href = '/auth/login';
    }
    return response;
};
