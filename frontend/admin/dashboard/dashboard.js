/**
 * Dashboard stats Alpine component.
 * Fetches data from the protected /admin/api/stats endpoint.
 */
function dashboardStats() {
    return {
        stats: {
            pages: 0,
            articles: 0,
            sites: 0,
            storage: 0,
            users: 0,
        },
        async init() {
            console.log('📊 [dashboardStats] Initializing…');
            const token = localStorage.getItem('anita_token');
            if (!token) {
                console.warn('🚫 [dashboardStats] No token found – stats will remain zero.');
                return;
            }

            try {
                const response = await fetch('/admin/api/stats', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    console.error(`❌ [dashboardStats] HTTP ${response.status}`);
                    return;
                }

                const data = await response.json();
                console.log('✅ [dashboardStats] Data received:', data);

                // Update stats (only the keys we have)
                this.stats.pages = data.pages ?? 0;
                this.stats.articles = data.articles ?? 0;
                this.stats.sites = data.sites ?? 0;
                this.stats.storage = data.storage ?? 0;
                this.stats.users = data.users ?? 0;  // Not shown but kept for later

            } catch (err) {
                console.error('💥 [dashboardStats] Network error:', err);
            }
        },
    };
}
