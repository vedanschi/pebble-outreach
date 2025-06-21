// frontend/src/pages/campaigns/[campaignId].tsx
import React from 'react';
import { useRouter } from 'next/router';
import AIChatWindow from '@/components/AIChat/AIChatWindow'; // Adjust path if necessary
// You might also want a layout component or other standard page elements
// import MainLayout from '@/components/Layout/MainLayout'; // Example

const CampaignDetailPage: React.FC = () => {
  const router = useRouter();
  const { campaignId } = router.query;

  // Ensure campaignId is a number if your component expects a number.
  // The value from router.query can be string or string[].
  const parsedCampaignId = parseInt(campaignId as string, 10);

  if (router.isFallback || !campaignId || isNaN(parsedCampaignId)) {
    return <div>Loading campaign details...</div>; // Or a proper loading spinner
  }

  return (
    // <MainLayout> // Example if you have a layout
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">
        AI Email Style Generator for Campaign #{parsedCampaignId}
      </h1>

      <div className="mb-6">
        {/* You could display other campaign details here if fetched */}
        <p>
          Use the chat interface below to define and refine the email style
          for this campaign with our AI assistant.
        </p>
      </div>

      <AIChatWindow campaignId={parsedCampaignId} />

      {/* You might want a link back to the campaigns list */}
      <div className="mt-6">
        <button
          onClick={() => router.push('/campaigns')}
          className="text-blue-500 hover:underline"
        >
          &larr; Back to Campaigns List
        </button>
      </div>
    </div>
    // </MainLayout>
  );
};

export default CampaignDetailPage;
