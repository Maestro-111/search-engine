document.addEventListener('DOMContentLoaded', function() {

    updateUserInterface();

    // Add logout event listener with null check
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

function updateUserInterface() {

    const userInfoDiv = document.getElementById('user-info');
    const loginSectionDiv = document.getElementById('login-section');
    const usernameSpan = document.getElementById('current-username');

    if (AuthManager.isLoggedIn()) {
        const user = AuthManager.getUser();
        if (user && usernameSpan) {
            usernameSpan.textContent = user.username;
            if (userInfoDiv) {
                userInfoDiv.style.display = 'block';
            }
            if (loginSectionDiv) {
                loginSectionDiv.style.display = 'none';
            }
        }
    } else {
        if (userInfoDiv) {
            userInfoDiv.style.display = 'none';
        }
        if (loginSectionDiv) {
            loginSectionDiv.style.display = 'block';
        }
    }
}

function logout() {
    AuthManager.clearTokens();
    updateUserInterface();
    alert('You have been logged out successfully!');
}
