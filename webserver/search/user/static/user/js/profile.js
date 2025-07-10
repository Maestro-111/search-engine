if (!AuthManager.isLoggedIn()) {
    window.location.href = '/auth/login/';
}

// Load profile data
async function loadProfile() {

    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const profileContent = document.getElementById('profile-content');

    try {
        loadingDiv.style.display = 'block';
        errorDiv.style.display = 'none';
        profileContent.style.display = 'none';

        const response = await AuthManager.makeAuthenticatedRequest('/auth/user/profile/');

        if (response.ok) {
            const data = await response.json();
            const user = data.user;

            document.getElementById('user-id').textContent = user.id;
            document.getElementById('user-username').textContent = user.username;
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-first-name').textContent = user.first_name || 'Not set';
            document.getElementById('user-last-name').textContent = user.last_name || 'Not set';
            document.getElementById('user-date-joined').textContent = new Date(user.date_joined).toLocaleDateString();

            loadingDiv.style.display = 'none';
            profileContent.style.display = 'block';

        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load profile');
        }

    } catch (error) {
        console.error('Error loading profile:', error);
        loadingDiv.style.display = 'none';
        errorDiv.style.display = 'block';
        errorDiv.textContent = 'Error loading profile: ' + error.message;
    }
}

function refreshProfile() {
    loadProfile();
}


function goToLogin() {
    window.location.href = '/auth/login/';
}


function goToMenu() {
    window.location.href = '/';
}



function logout() {
    AuthManager.clearTokens();
    window.location.href = '/auth/login/';
}

loadProfile();
