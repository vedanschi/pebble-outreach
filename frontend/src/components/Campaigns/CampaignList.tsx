import React, { useEffect, useState } from 'react';
import { fetchCampaigns } from '../../utils/api';

const CampaignList: React.FC = () => {
    const [campaigns, setCampaigns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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
            <h2>Campaigns</h2>
            <ul>
                {campaigns.map((campaign) => (
                    <li key={campaign.id}>
                        <h3>{campaign.name}</h3>
                        <p>{campaign.description}</p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default CampaignList;