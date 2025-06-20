import React, { useEffect, useState } from 'react';
import { fetchFollowUps } from '../../utils/api';

interface FollowUp {
    id: number;
    subject: string;
    body: string;
    delay: number;
    createdAt?: string;
}

interface FollowUpListProps {
    campaignId: number;
}

const FollowUpList: React.FC<FollowUpListProps> = ({ campaignId }) => {
    const [followUps, setFollowUps] = useState<FollowUp[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadFollowUps = async () => {
            try {
                const data = await fetchFollowUps(campaignId);
                setFollowUps(data);
            } catch (err) {
                setError('Failed to load follow-ups');
            } finally {
                setLoading(false);
            }
        };

        loadFollowUps();
    }, [campaignId]);

    if (loading) {
        return <div>Loading follow-ups...</div>;
    }

    if (error) {
        return <div className="text-red-500">{error}</div>;
    }

    return (
        <div>
            <h2 className="text-lg font-semibold mb-2">Follow-Up Rules</h2>
            {followUps.length === 0 ? (
                <div className="text-gray-400">No follow-up rules yet.</div>
            ) : (
                <ul className="space-y-2">
                    {followUps.map((followUp) => (
                        <li key={followUp.id} className="border rounded p-3 bg-purple-50">
                            <div className="font-bold">{followUp.subject}</div>
                            <div className="text-sm text-gray-600 mb-1">Delay: {followUp.delay} day(s)</div>
                            <div className="text-gray-700 whitespace-pre-line mb-1">{followUp.body}</div>
                            {followUp.createdAt && (
                                <div className="text-xs text-gray-400">Created: {new Date(followUp.createdAt).toLocaleString()}</div>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default FollowUpList;