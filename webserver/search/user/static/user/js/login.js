document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageElement = document.getElementById('message');

    // Clear previous messages
    messageElement.innerHTML = '';

    // Client-side validation
    const validationErrors = validateLoginForm(username, password);

    if (validationErrors.length > 0) {
        // Show validation errors
        const errorHtml = validationErrors.map(error =>
            `<p style="color: red;">• ${error}</p>`
        ).join('');
        messageElement.innerHTML = errorHtml;
        return;
    }

    // Show loading state
    messageElement.innerHTML = '<p style="color: blue;">Logging in...</p>';

    try {
        const response = await fetch('/auth/login/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });

        const data = await response.json();

        if (response.ok) {
            // Store tokens
            AuthManager.setTokens(
                data.access_token,
                data.refresh_token,
                data.user
            );

            // Show success message briefly
            messageElement.innerHTML =
                `<p style="color: green;">${data.message} Redirecting to main menu...</p>`;

            // Redirect to main menu after 1 second
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);

        } else {
            messageElement.innerHTML =
                `<p style="color: red;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        messageElement.innerHTML =
            `<p style="color: red;">Error: ${error.message}</p>`;
    }
});

function validateLoginForm(username, password) {

    const errors = [];

    if (!username || username.trim() === '') {
        errors.push('Username is required');
    } else if (username.length < 3) {
        errors.push('Username must be at least 3 characters long');
    } else if (username.length > 50) {
        errors.push('Username must be less than 50 characters');
    } else if (!/^[a-zA-Z0-9@._-]+$/.test(username)) {
        errors.push('Username can only contain letters, numbers, @, ., _, and -');
    }

    if (!password || password.trim() === '') {
        errors.push('Password is required');
    } else if (password.length < 6) {
        errors.push('Password must be at least 6 characters long');
    } else if (password.length > 128) {
        errors.push('Password must be less than 128 characters');
    }

    return errors;
}
