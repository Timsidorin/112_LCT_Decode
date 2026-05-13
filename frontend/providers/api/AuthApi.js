import axios from 'axios';

export class AuthApi {
    getMe() {
        const token = localStorage.getItem('tokenAuth');
        return axios.get('/api/auth/me/', {
            headers: { Authorization: `Bearer ${token}` }
        });
    }
}

export const authApi = new AuthApi();