import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { fetchCampaigns } from '../../utils/api';

type Campaign = {
    id: string;
    name: string;
    description: string;
    status: string;
};

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
        return <div>{error}</div>;
    }

    return (
        <div>
            <h2 className="text-2xl font-bold mb-4">Campaigns</h2>
            <ul className="space-y-4">
                {campaigns.map((campaign) => (
                    <li
                        key={campaign.id}
                        className="p-4 border rounded shadow hover:bg-gray-50 cursor-pointer transition"
                        onClick={() => router.push(`/campaigns/${campaign.id}`)}
                    >
                        <div className="flex justify-between items-center">
                            <div>
                                <h3 className="text-lg font-semibold">{campaign.name}</h3>
                                <p className="text-gray-600">{campaign.description}</p>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${campaign.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'}`}>
                                {campaign.status}
                            </span>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default CampaignList;