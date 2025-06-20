// frontend/src/pages/campaigns/[campaignId].tsx
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import AIChatWindow from '@/components/AIChat/AIChatWindow';
import CSVUploadForm from '@/components/CSVUpload/CSVUploadForm';
import EmailGenerator from '@/components/EmailGeneration/EmailGenerator';
import FollowUpList from '@/components/FollowUp/FollowUpList';
import FollowUpForm from '@/components/FollowUp/FollowUpForm';
// import EmailSendControls from '@/components/EmailGeneration/EmailSendControls'; // To be implemented
// import EmailTrackingTable from '@/components/EmailGeneration/EmailTrackingTable'; // To be implemented
import { getCampaignDetails, getSentEmails } from '@/utils/api';
import type { Campaign, SentEmail } from '@/types';

const CampaignDetailPage: React.FC = () => {
  const router = useRouter();
  const { campaignId } = router.query;
  const parsedCampaignId = parseInt(campaignId as string, 10);

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [sentEmails, setSentEmails] = useState<SentEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFollowUpForm, setShowFollowUpForm] = useState(false);

  useEffect(() => {
    if (!parsedCampaignId || isNaN(parsedCampaignId)) return;
    setLoading(true);
    Promise.all([
      getCampaignDetails(parsedCampaignId),
      getSentEmails(parsedCampaignId),
    ])
      .then(([campaignData, sentEmailsData]) => {
        setCampaign(campaignData);
        setSentEmails(sentEmailsData);
        setLoading(false);
      })
      .catch((err) => {
        setError('Failed to load campaign details.');
        setLoading(false);
      });
  }, [parsedCampaignId]);

  if (router.isFallback || !campaignId || isNaN(parsedCampaignId) || loading) {
    return <div>Loading campaign details...</div>;
  }
  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-2">
        Campaign: {campaign?.name || `#${parsedCampaignId}`}
      </h1>
      <div className="mb-4 text-gray-500">
        <span>Created: {campaign?.createdAt ? new Date(campaign.createdAt).toLocaleString() : '-'}</span>
        <span className="ml-4">Contacts: {campaign?.contactsCount ?? (campaign?.contacts ? campaign.contacts.length : '-')}</span>
        <span className="ml-4">Emails Sent: {campaign?.emailsSent ? campaign.emailsSent.length : '-'}</span>
        <span className="ml-4">Opens: {campaign?.opensCount ?? '-'}</span>
      </div>

      {/* CSV Upload Section */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Upload Contacts (CSV)</h2>
        {/* Ensure CSVUploadForm accepts campaignId as prop */}
        <CSVUploadForm campaignId={parsedCampaignId} />
      </section>

      {/* AI Chat Section */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">AI Email Style Generator</h2>
        <p className="mb-2 text-gray-600">
          Use the chat interface below to define and refine the email style for this campaign with our AI assistant.
        </p>
        <AIChatWindow campaignId={parsedCampaignId} />
      </section>

      {/* Email Generator Section */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">AI Email Generator (Prompt-based)</h2>
        <EmailGenerator />
      </section>

      {/* Email Sending Controls */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Send Emails</h2>
        {/* <EmailSendControls campaignId={parsedCampaignId} /> */}
        <div className="bg-purple-50 border border-purple-200 rounded p-4 text-purple-700">
          [Email sending controls coming soon]
        </div>
      </section>

      {/* Follow-up Manager */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-semibold">Follow-ups</h2>
          <button
            className="bg-purple-600 text-white px-3 py-1 rounded hover:bg-purple-700"
            onClick={() => setShowFollowUpForm((v) => !v)}
          >
            {showFollowUpForm ? 'Cancel' : 'Add Follow-Up'}
          </button>
        </div>
        {showFollowUpForm && (
          <div className="mb-4">
            {/* Ensure FollowUpForm accepts campaignId as prop */}
            <FollowUpForm campaignId={parsedCampaignId} onSubmit={() => setShowFollowUpForm(false)} />
          </div>
        )}
        {/* Ensure FollowUpList accepts campaignId as prop */}
        <FollowUpList campaignId={parsedCampaignId} />
      </section>

      {/* Sent Emails & Tracking */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Sent Emails & Tracking</h2>
        {/* <EmailTrackingTable sentEmails={sentEmails} /> */}
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded">
            <thead>
              <tr>
                <th className="px-4 py-2 border-b">Recipient</th>
                <th className="px-4 py-2 border-b">Subject</th>
                <th className="px-4 py-2 border-b">Sent At</th>
                <th className="px-4 py-2 border-b">Opened?</th>
                <th className="px-4 py-2 border-b">Opens</th>
              </tr>
            </thead>
            <tbody>
              {sentEmails.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-4 text-gray-400">
                    No emails sent yet.
                  </td>
                </tr>
              ) : (
                sentEmails.map((email) => (
                  <tr key={email.id}>
                    <td className="px-4 py-2 border-b">{email.recipient || email.to || '-'}</td>
                    <td className="px-4 py-2 border-b">{email.subject}</td>
                    <td className="px-4 py-2 border-b">{email.sentAt ? new Date(email.sentAt).toLocaleString() : '-'}</td>
                    <td className="px-4 py-2 border-b">{email.openedAt ? 'Yes' : 'No'}</td>
                    <td className="px-4 py-2 border-b">{email.opensCount ?? email.opens ?? 0}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Back to Campaigns List */}
      <div className="mt-6">
        <button
          onClick={() => router.push('/campaigns')}
          className="text-blue-500 hover:underline"
        >
          &larr; Back to Campaigns List
        </button>
      </div>
    </div>
  );
};

export default CampaignDetailPage;
