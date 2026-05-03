// Global admin application state
function adminApp() {
    return {
        authenticated: false,
        loading: false,
        loadingMessage: 'Loading...',
        user: null,
        sidebarOpen: true,

        async init() {
            this.loading = true;
            this.loadingMessage = 'Checking authentication...';

            try {
                const token = localStorage.getItem('anita_token');
                const pbUrl = localStorage.getItem('anita_pb_url') || 'http://127.0.0.1:8090';

                if (!token) {
                    this.authenticated = false;
                    this.loading = false;
                    return;
                }

                // Validate token directly against PocketBase
                const response = await fetch(`${pbUrl}/api/collections/_superusers/auth-refresh`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    const data = await response.json();
                    this.user = data.record;
                    this.authenticated = true;

                    // Refresh token in storage
                    if (data.token) {
                        localStorage.setItem('anita_token', data.token);
                    }
                } else {
                    localStorage.removeItem('anita_token');
                    this.authenticated = false;
                }
            } catch (err) {
                console.error('Auth check failed:', err);
                this.authenticated = false;
            } finally {
                this.loading = false;
            }
        },


        logout() {
            localStorage.removeItem('anita_token');
            window.location.href = '/auth/login';
        },
    };
}
