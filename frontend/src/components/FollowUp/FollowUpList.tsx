import React, { useEffect, useState } from 'react';
import { fetchFollowUps } from '../../utils/api';

const FollowUpList: React.FC = () => {
    const [followUps, setFollowUps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadFollowUps = async () => {
            try {
                const data = await fetchFollowUps();
                setFollowUps(data);
            } catch (err) {
                setError('Failed to load follow-ups');
            } finally {
                setLoading(false);
            }
        };

        loadFollowUps();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <h2>Follow-Up Rules</h2>
            <ul>
                {followUps.map((followUp) => (
                    <li key={followUp.id}>
                        <h3>{followUp.name}</h3>
                        <p>{followUp.description}</p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default FollowUpList;