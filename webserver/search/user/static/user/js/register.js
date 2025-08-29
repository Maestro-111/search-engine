document.getElementById('registerForm').addEventListener('submit', async (e) => {

    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const messageElement = document.getElementById('message');

    messageElement.innerHTML = '';
    const validationErrors = validateLoginForm(username, password);

    if (validationErrors.length > 0) {
        // Show validation errors
        const errorHtml = validationErrors.map(error =>
            `<p style="color: red;">• ${error}</p>`
        ).join('');
        messageElement.innerHTML = errorHtml;
        return;
    }

    try {
        const response = await fetch('/auth/register/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, email, password})
        });

        const data = await response.json();

        if (response.ok) {
            // Store tokens
            AuthManager.setTokens(
                data.access_token,
                data.refresh_token,
                data.user
            );

            window.location.href = '/auth/user/profile/';

        } else {
            document.getElementById('message').innerHTML =
                `<p style="color: red;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        document.getElementById('message').innerHTML =
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

    if (username.includes('@')) {
        if (!isValidEmail(username)) {
            errors.push('Please enter a valid email address');
        }
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

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
