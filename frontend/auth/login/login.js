function loginForm() {
    return {
        email: '',
        password: '',
        remember: false,
        showPassword: false,
        loading: false,
        error: '',
        success: '',
        fieldErrors: {},

        async handleLogin(event) {
            this.loading = true;
            this.error = '';
            this.fieldErrors = {};

            const form = event.target;
            const formData = new FormData(form);

            try {
                const response = await fetch('/api/auth/login', {  // ← Hardcode the URL
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: this.email,
                        password: this.password,
                        remember: this.remember,
                    }),
                });


                const data = await response.json();

                if (response.ok) {
                    this.success = 'Login successful! Redirecting...';
                    console.log('Login Success!')
                    console.log("Raw Data...")
                    console.log(data)
                    console.log("Checking Token...")
                    console.log(data.token)
                    console.log("Checking User...")
                    console.log(data.user)
                    // Store token
                    localStorage.setItem('anita_token', data.token);
                    localStorage.setItem('anita_user', JSON.stringify(data.user));

                    // // Redirect to admin dashboard
                    // setTimeout(() => {
                    //     window.location.href = '/admin/dashboard';
                    // }, 500);
                } else {
                    // Handle validation errors
                    if (data.data) {
                        for (const [field, msg] of Object.entries(data.data)) {
                            this.fieldErrors[field] = typeof msg === 'object' ? msg.message : msg;
                        }
                    }
                    this.error = data.message || 'Invalid email or password.';
                }
            } catch (err) {
                this.error = 'Connection error. Please try again.';
            } finally {
                this.loading = false;
            }
        },
    };
}
