// frontend/src/utils/aiChatApi.ts
import apiClient from './api';

export interface ApiChatMessage {
  role: string;
  content: string;
}

export interface AIChatResponsePayload {
  reply: string;
  conversation_history: ApiChatMessage[];
}

// This interface matches the backend's FinalizeEmailStyleResponse schema
export interface FinalizeStyleApiResponse {
    message: string;
    email_template_id?: number;
    // The backend schema for FinalizeEmailStyleResponse is minimal:
    // message, email_template_id, preview_subject, preview_body.
    // It does NOT include subject_template or body_template directly from the template.
    // If those are needed on the frontend after this call, a separate fetch for the template would be required.
    preview_subject?: string | null;
    preview_body?: string | null;
}

export const sendChatMessage = async (
  campaignId: number,
  messages: ApiChatMessage[]
): Promise<AIChatResponsePayload> => {
  const response = await apiClient.post<AIChatResponsePayload>('/api/v1/ai-chat/conversation', {
    campaign_id: campaignId,
    messages,
  });
  return response.data;
};

export const finalizeStyle = async (
  campaignId: number,
  finalConversation: ApiChatMessage[],
  contactIdForPreview?: number
): Promise<FinalizeStyleApiResponse> => { // Updated return type
  const response = await apiClient.post<FinalizeStyleApiResponse>('/api/v1/ai-chat/finalize-style', { // Updated expected type
    campaign_id: campaignId,
    final_conversation: finalConversation,
    contact_id_for_preview: contactIdForPreview,
  });
  return response.data;
};
