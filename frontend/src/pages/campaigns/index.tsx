import React from 'react';
import CampaignList from '../../components/Campaigns/CampaignList';

const CampaignsPage: React.FC = () => {
    return (
        <div>
            <h1>Campaigns</h1>
            <CampaignList />
        </div>
    );
};

export default CampaignsPage;