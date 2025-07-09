document.getElementById('loginForm').addEventListener('submit', async (e) => {

    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

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
            document.getElementById('message').innerHTML =
                `<p style="color: green;">${data.message} Redirecting to main menu...</p>`;

            // Redirect to main menu after 1 second
            setTimeout(() => {
                window.location.href = '/';  // Or wherever your main page is
            }, 1000);

        } else {
            document.getElementById('message').innerHTML =
                `<p style="color: red;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        document.getElementById('message').innerHTML =
            `<p style="color: red;">Error: ${error.message}</p>`;
    }
});
