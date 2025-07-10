document.getElementById('registerForm').addEventListener('submit', async (e) => {

    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

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
