import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { UserProfile } from '../types';

export const Dashboard: React.FC = () => {
    const [user, setUser] = useState<UserProfile | null>(null);

    useEffect(() => {
        ApiClient.getProfile("alex").then(setUser);
    }, []);

    return (
        <div className="vault-dashboard">
            <h1>Welcome, {user?.username}</h1>
        </div>
    );
};
