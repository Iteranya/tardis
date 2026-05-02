function registerForm() {
    return {
        username: '',
        email: '',
        password: '',
        passwordConfirm: '',
        showPassword: false,
        loading: false,
        error: '',
        success: '',
        fieldErrors: {},

        // Password strength
        strength: 0,
        strengthClasses: 'bg-gray-200',

        get hasMinLength() { return this.password.length >= 8; },
        get hasUpper() { return /[A-Z]/.test(this.password); },
        get hasNumber() { return /[0-9]/.test(this.password); },
        get passwordsMatch() {
            return !this.passwordConfirm || this.password === this.passwordConfirm;
        },

        checkPasswordStrength() {
            let score = 0;
            if (this.hasMinLength) score += 25;
            if (this.hasUpper) score += 25;
            if (this.hasNumber) score += 25;
            if (/[^a-zA-Z0-9]/.test(this.password)) score += 25;

            this.strength = score;

            if (score <= 25) this.strengthClasses = 'bg-red-500';
            else if (score <= 50) this.strengthClasses = 'bg-orange-500';
            else if (score <= 75) this.strengthClasses = 'bg-yellow-500';
            else this.strengthClasses = 'bg-green-500';
        },

        async handleRegister(event) {
            this.loading = true;
            this.error = '';
            this.fieldErrors = {};

            if (this.password !== this.passwordConfirm) {
                this.error = 'Passwords do not match!';
                this.loading = false;
                return;
            }

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: this.username,
                        email: this.email,
                        password: this.password,
                        passwordConfirm: this.passwordConfirm,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    this.success = 'Account created! Redirecting to login...';
                    setTimeout(() => {
                        window.location.href = '/auth/login';
                    }, 1500);
                } else {
                    if (data.data) {
                        for (const [field, msg] of Object.entries(data.data)) {
                            this.fieldErrors[field] = typeof msg === 'object' ? msg.message : msg;
                        }
                    }
                    this.error = data.message || 'Registration failed.';
                }
            } catch (err) {
                this.error = 'Connection error. Please try again.';
            } finally {
                this.loading = false;
            }
        },
    };
}
