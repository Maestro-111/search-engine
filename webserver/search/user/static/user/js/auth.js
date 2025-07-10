class AuthManager {
    static TOKEN_KEY = 'access_token';
    static REFRESH_KEY = 'refresh_token';
    static USER_KEY = 'user_info';

    // Store tokens after successful login/register
    static setTokens(accessToken, refreshToken, user = null) {
        localStorage.setItem(this.TOKEN_KEY, accessToken);
        localStorage.setItem(this.REFRESH_KEY, refreshToken);

        if (user) {
            localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        }

        console.log('Tokens stored successfully');
    }

    // Get stored tokens
    static getAccessToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    static getRefreshToken() {
        return localStorage.getItem(this.REFRESH_KEY);
    }

    static getUser() {
        const userStr = localStorage.getItem(this.USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    }

    static isLoggedIn() {
        return !!this.getAccessToken();
    }

    static clearTokens() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_KEY);
        localStorage.removeItem(this.USER_KEY);
        console.log('Tokens cleared');
    }

    static async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getAccessToken();

        if (!token) {
            throw new Error('No access token available');
        }

        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            const errorData = await response.json();

            if (errorData.error === 'Token has expired') {
                console.log('Token expired, attempting refresh...');

                const refreshSuccess = await this.refreshAccessToken();
                if (refreshSuccess) {
                    const newToken = this.getAccessToken();
                    return fetch(url, {
                        ...options,
                        headers: {
                            ...options.headers,
                            'Authorization': `Bearer ${newToken}`,
                            'Content-Type': 'application/json'
                        }
                    });
                } else {
                    this.handleAuthFailure();
                    throw new Error('Authentication failed');
                }
            } else {
                this.handleAuthFailure();
                throw new Error(errorData.error || 'Authentication failed');
            }
        }

        return response;
    }

    static async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();

        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch('/auth/refresh/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({refresh_token: refreshToken})
            });

            if (response.ok) {
                const data = await response.json();
                // Update access token (keep same refresh token)
                localStorage.setItem(this.TOKEN_KEY, data.access_token);
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            return false;
        }
    }

    static handleAuthFailure() {
        this.clearTokens();
        window.location.href = '/auth/login/';
    }
}
