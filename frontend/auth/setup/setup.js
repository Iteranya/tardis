function setupForm() {
    return {
        // Step management
        step: 1,
        loading: false,
        error: '',
        success: '',

        // Step 1: PocketBase connection
        testing: false,
        connectionTested: false,
        connectionOk: false,
        pbVersion: '?',

        pocketbase: {
            url: 'http://localhost:8090',
        },

        // Step 2: Admin account
        admin: {
            email: '',
            password: '',
        },

        // Step 3: Site info
        site: {
            name: '',
            url: '',
        },

        // Step 4: Results
        setupError: '',

        // ─── Test PocketBase Connection ───
        async testConnection() {
            this.testing = true;
            this.error = '';
            this.connectionTested = false;

            try {
                const response = await fetch('/api/setup/test-connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: this.pocketbase.url,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    this.connectionOk = true;
                    this.pbVersion = data.version || '?';
                } else {
                    this.connectionOk = false;
                    this.error = data.message || 'Connection failed.';
                }
            } catch (err) {
                this.connectionOk = false;
                this.error = 'Cannot reach PocketBase. Check the URL and try again.';
            } finally {
                this.testing = false;
                this.connectionTested = true;
            }
        },

        // ─── Complete Setup ───
        async completeSetup() {
            this.loading = true;
            this.setupError = '';
            this.error = '';

            try {
                const response = await fetch('/api/setup/initialize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pocketbase: this.pocketbase,
                        admin: this.admin,
                        site: this.site,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    // Store credentials
                    localStorage.setItem('anita_token', data.token);
                    localStorage.setItem('anita_url', this.pocketbase.url);

                    // Move to completion step
                    this.step = 4;
                } else {
                    this.setupError = data.message || 'Setup failed. Please try again.';
                    // Stay on step 3 but show error
                }
            } catch (err) {
                this.setupError = 'Connection error during setup. Please try again.';
            } finally {
                this.loading = false;
            }
        },

        // ─── Go to Dashboard ───
        goToDashboard() {
            window.location.href = '/admin/dashboard';
        },
    };
}
