import React from 'react';

const CampaignDetails: React.FC<{ campaign: any }> = ({ campaign }) => {
    if (!campaign) {
        return <div>No campaign selected.</div>;
    }

    return (
        <div className="bg-white rounded shadow p-6">
            <h2 className="text-2xl font-bold mb-2">{campaign.name}</h2>
            <p className="mb-2"><strong>Description:</strong> {campaign.description}</p>
            <p className="mb-2"><strong>Status:</strong> {campaign.status}</p>
            <p className="mb-2"><strong>Created At:</strong> {new Date(campaign.createdAt).toLocaleDateString()}</p>
            <p className="mb-4"><strong>Last Updated:</strong> {new Date(campaign.updatedAt).toLocaleDateString()}</p>
            <h3 className="text-lg font-semibold mb-2">Emails Sent</h3>
            <ul className="list-disc pl-5">
                {campaign.emailsSent && campaign.emailsSent.length > 0 ? (
                    campaign.emailsSent.map((email: any) => (
                        <li key={email.id}>
                            <span className="font-medium">{email.subject}</span> - {new Date(email.sentAt).toLocaleString()}
                        </li>
                    ))
                ) : (
                    <li className="text-gray-500">No emails sent yet.</li>
                )}
            </ul>
        </div>
    );
};

export default CampaignDetails;