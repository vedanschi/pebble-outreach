// frontend/src/components/AIChat/ChatMessage.tsx
import React from 'react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ role, content }) => {
  const messageClass = role === 'user' ? 'text-right' : 'text-left';
  const bubbleClass = role === 'user'
    ? 'bg-blue-500 text-white self-end'
    : 'bg-gray-200 text-gray-800 self-start';

  return (
    <div className={`my-2 flex ${role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`p-3 rounded-lg max-w-md ${bubbleClass}`}>
        <p className="text-sm whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
};

export default ChatMessage;
