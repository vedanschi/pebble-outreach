import React from 'react';

const CampaignDetails: React.FC<{ campaign: any }> = ({ campaign }) => {
    if (!campaign) {
        return <div>No campaign selected.</div>;
    }

    return (
        <div>
            <h2>{campaign.name}</h2>
            <p><strong>Description:</strong> {campaign.description}</p>
            <p><strong>Status:</strong> {campaign.status}</p>
            <p><strong>Created At:</strong> {new Date(campaign.createdAt).toLocaleDateString()}</p>
            <p><strong>Last Updated:</strong> {new Date(campaign.updatedAt).toLocaleDateString()}</p>
            <h3>Emails Sent:</h3>
            <ul>
                {campaign.emailsSent.map((email: any) => (
                    <li key={email.id}>{email.subject} - {email.sentAt}</li>
                ))}
            </ul>
        </div>
    );
};

export default CampaignDetails;