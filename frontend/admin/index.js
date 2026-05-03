// ========================================
// Aina-chan's Admin Shell App (◕‿◕✿)
// ========================================

// Notification store (Alpine)
document.addEventListener('alpine:init', () => {
    Alpine.data('notificationManager', () => ({
        notifications: [],
        add(type, message) {
            const id = Date.now() + Math.random();
            this.notifications.push({ id, type, message });
            setTimeout(() => this.remove(id), 4000);
        },
        remove(id) {
            this.notifications = this.notifications.filter(n => n.id !== id);
        }
    }));

    Alpine.data('adminApp', () => ({
        user: null,
        loading: false,
        currentPage: 'dashboard',

        async init() {
            // Check authentication
            const token = localStorage.getItem('anita_token');
            if (!token) {
                window.location.href = '/auth/login';
                return;
            }

            try {
                const res = await fetch('/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Unauthorized');
                const data = await res.json();
                this.user = data.user;
                // Load initial page
                this.navigate(this.currentPage);
            } catch (e) {
                localStorage.removeItem('anita_token');
                window.location.href = '/auth/login';
            }
        },

        async navigate(page) {
            this.currentPage = page;
            this.loading = true;
            const target = document.getElementById('main-content');

            try {
                // Fetch the module HTML from static directory
                const response = await fetch(`/static/admin/${page}/${page}.html`);
                if (!response.ok) throw new Error('Page not found');
                const html = await response.text();
                target.innerHTML = html;

                // Execute any inline scripts in the loaded content
                const scripts = target.querySelectorAll('script');
                scripts.forEach(oldScript => {
                    const newScript = document.createElement('script');
                    Array.from(oldScript.attributes).forEach(attr => {
                        newScript.setAttribute(attr.name, attr.value);
                    });
                    newScript.textContent = oldScript.textContent;
                    oldScript.parentNode.replaceChild(newScript, oldScript);
                });

                // Also load the module's JS file (if any)
                const moduleScript = document.createElement('script');
                moduleScript.src = `/static/admin/${page}/${page}.js`;
                moduleScript.onload = () => {
                    // Optional: call module init if exists
                    if (window[`${page}Module`] && window[`${page}Module`].init) {
                        window[`${page}Module`].init();
                    }
                };
                document.body.appendChild(moduleScript);
            } catch (err) {
                target.innerHTML = `<div class="error">Failed to load ${page} module.</div>`;
            } finally {
                this.loading = false;
            }
        },

        logout() {
            localStorage.removeItem('anita_token');
            window.location.href = '/auth/login';
        }
    }));
});
