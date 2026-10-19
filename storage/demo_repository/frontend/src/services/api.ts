import { UserProfile } from '../types';

export class ApiClient {
    static async getProfile(username: string): Promise<UserProfile> {
        const response = await fetch(`/api/v1/auth/user/${username}`);
        return response.json();
    }
}
