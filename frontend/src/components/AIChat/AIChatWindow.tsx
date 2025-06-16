// frontend/src/components/AIChat/AIChatWindow.tsx
import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { sendChatMessage, finalizeStyle } from '@/utils/aiChatApi';
import type { ApiChatMessage, FinalizeStyleApiResponse } from '@/utils/aiChatApi'; // Import FinalizeStyleApiResponse

export interface ChatMessageData {
  role: 'user' | 'assistant';
  content: string;
}

interface AIChatWindowProps {
  campaignId: number; // Or string
}

const AIChatWindow: React.FC<AIChatWindowProps> = ({ campaignId }) => {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewSubject, setPreviewSubject] = useState<string | null>(null);
  const [previewBody, setPreviewBody] = useState<string | null>(null);

  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
     setMessages([
         { role: 'assistant', content: `Hi there! I'm here to help you define the email style for Campaign ID: ${campaignId}. What kind of email are you looking to create? (e.g., tone, key message, target audience action)` }
     ]);
     setPreviewSubject(null); // Clear preview on new campaign ID
     setPreviewBody(null);
  }, [campaignId]);

  const handleSendMessage = async (userInput: string) => {
    const userMessage: ChatMessageData = { role: 'user', content: userInput };
    const currentMessagesStateBeforeApiCall: ChatMessageData[] = [...messages, userMessage];
    setMessages(currentMessagesStateBeforeApiCall);
    setIsLoading(true);
    setError(null);

    try {
      const apiMessages: ApiChatMessage[] = currentMessagesStateBeforeApiCall.map(m => ({ role: m.role, content: m.content }));
      const response = await sendChatMessage(campaignId, apiMessages);
      setMessages(response.conversation_history.map(m => ({ role: m.role as 'user' | 'assistant', content: m.content })));
    } catch (err: any) {
      setError(err.message || 'Failed to send message. Please try again.');
      setMessages(messages);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFinalizeStyle = async () => {
    if (messages.length < 2) {
      setError("Please interact with the AI first to define a style.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setPreviewSubject(null); // Clear previous preview
    setPreviewBody(null);

    try {
      const apiMessages: ApiChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }));
      // Using placeholder contact ID 1 for preview generation.
      // This should be made dynamic in a real application.
      const contactIdForPreview = 1;

      const response = await finalizeStyle(campaignId, apiMessages, contactIdForPreview);

      const successMessageContent = response.message || `Successfully finalized style! New Email Template ID: ${response.email_template_id}.`;
      const successMessageChat: ChatMessageData = {
        role: 'assistant',
        content: successMessageContent
      };
      setMessages(prevMessages => [...prevMessages, successMessageChat]);

      if (response.preview_subject && response.preview_body) {
          setPreviewSubject(response.preview_subject);
          setPreviewBody(response.preview_body);
          alert(`Style finalized! Template ID: ${response.email_template_id}. Preview available.`);
      } else {
          alert(`Style finalized! Template ID: ${response.email_template_id}. No preview generated this time (contact ID ${contactIdForPreview} might not be valid for this campaign or an error occurred during preview generation).`);
      }

    } catch (err: any) {
      setError(err.message || 'Failed to finalize style. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[700px] border rounded-lg shadow-lg"> {/* Increased height slightly for preview */}
      <div className="flex-grow p-4 overflow-y-auto bg-gray-50 min-h-[300px]"> {/* Min height for chat area */}
        {messages.map((msg, index) => (
          <ChatMessage key={index} role={msg.role} content={msg.content} />
        ))}
        <div ref={messagesEndRef} />
      </div>
      {error && <div className="p-2 text-red-500 text-center">{error}</div>}
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      <div className="p-4 border-t text-center">
         <button
             onClick={handleFinalizeStyle}
             className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400"
             disabled={isLoading || messages.length < 2}
         >
             Finalize Email Style & Generate Preview
         </button>
      </div>
      {previewSubject && previewBody && (
        <div className="p-4 border-t mt-0 bg-gray-100 rounded-b-lg"> {/* Adjusted mt-0 and rounded-b-lg */}
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Personalized Preview (Contact ID: 1):</h3>
          <div className="p-3 border rounded bg-white shadow-sm">
            <p className="text-sm font-medium text-gray-700">Subject: {previewSubject}</p>
            <hr className="my-2" />
            <div
              className="text-sm text-gray-800 whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ __html: previewBody.replace(/\n/g, '<br />') }}
            />
          </div>
          <button
              onClick={() => { setPreviewSubject(null); setPreviewBody(null); }}
              className="mt-3 text-sm text-blue-500 hover:underline"
          >
              Clear Preview
          </button>
        </div>
      )}
    </div>
  );
};

export default AIChatWindow;
