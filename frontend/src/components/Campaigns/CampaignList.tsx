import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { fetchCampaigns } from '../../utils/api';
import type { Campaign } from '../../types';

const CampaignList: React.FC = () => {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    useEffect(() => {
        const getCampaigns = async () => {
            try {
                const data = await fetchCampaigns();
                setCampaigns(data);
            } catch (err) {
                setError('Failed to fetch campaigns');
            } finally {
                setLoading(false);
            }
        };

        getCampaigns();
    }, []);

    if (loading) {
        return <div>Loading campaigns...</div>;
    }

    if (error) {
        return <div className="text-red-500">{error}</div>;
    }

    return (
        <div className="max-w-2xl mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">Campaigns</h2>
            <ul className="space-y-4">
                {campaigns.map((campaign) => (
                    <li
                        key={campaign.id}
                        className="bg-white rounded shadow p-4 hover:bg-purple-50 cursor-pointer transition"
                        onClick={() => router.push(`/campaigns/${campaign.id}`)}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold">{campaign.name}</h3>
                                <p className="text-gray-600 mb-1">{campaign.description}</p>
                                <span className="text-xs text-gray-400">Created: {new Date(campaign.createdAt).toLocaleDateString()}</span>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${campaign.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{campaign.status}</span>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default CampaignList;