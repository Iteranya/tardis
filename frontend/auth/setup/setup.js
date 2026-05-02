function setupForm() {
    return {
        step: 1,
        loading: false,
        error: '',
        success: '',
        setupError: '',

        // Step 1
        testing: false,
        connectionTested: false,
        connectionOk: false,
        pbVersion: '?',
        pocketbase: { url: 'http://localhost:8090' },

        // Step 2
        admin: { email: '', password: '' },

        // ─── Test Connection ───
        async testConnection() {
            this.testing = true;
            this.error = '';

            try {
                const response = await fetch('/api/setup/test-connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: this.pocketbase.url }),
                });
                const data = await response.json();
                if (response.ok) {
                    this.connectionOk = true;
                    this.pbVersion = data.version || '?';
                } else {
                    this.connectionOk = false;
                    this.error = data.message || 'Connection failed.';
                }
            } catch {
                this.connectionOk = false;
                this.error = 'Cannot reach PocketBase.';
            } finally {
                this.testing = false;
                this.connectionTested = true;
            }
        },

        // ─── Validate Superuser + Init Collections ───
        async completeSetup() {
            this.loading = true;
            this.setupError = '';

            try {
                // Step A: Validate credentials (just checks if login works)
                const validateRes = await fetch('/api/setup/validate-credentials', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: this.pocketbase.url,
                        email: this.admin.email,
                        password: this.admin.password,
                    }),
                });
                const validateData = await validateRes.json();
                if (!validateRes.ok) throw new Error(validateData.detail || 'Invalid credentials');

                // Step B: Save credentials to secrets.json
                const saveRes = await fetch('/api/setup/save-credentials', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: this.pocketbase.url,
                        email: this.admin.email,
                        password: this.admin.password,
                    }),
                });
                const saveData = await saveRes.json();
                if (!saveRes.ok) throw new Error(saveData.message || 'Failed to save credentials');

                // Step C: Initialize collections
                const initRes = await fetch('/api/setup/initialize-collections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                });
                const initData = await initRes.json();
                if (!initRes.ok) throw new Error(initData.message);

                this.step = 3; // Done!

            } catch (err) {
                this.setupError = err.message || 'Setup failed.';
            } finally {
                this.loading = false;
            }
        },

        goToLogin() {
            window.location.href = '/auth/login';
        },
    };
}
