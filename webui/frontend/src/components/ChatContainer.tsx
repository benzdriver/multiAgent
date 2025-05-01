import React, { useState } from 'react';
import styled from 'styled-components';
import Button from './common/Button';
import Card from './common/Card';

const ChatWrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background-color: white;
`;


const ChatMessages = styled.div`
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const MessageBubble = styled.div<{ isUser: boolean }>`
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 18px;
  align-self: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  background-color: ${props => props.isUser ? 'var(--primary-color)' : '#f0f0f0'};
  color: ${props => props.isUser ? 'white' : 'var(--text-color)'};
  word-break: break-word;
`;

const ChatInputContainer = styled.div`
  display: flex;
  padding: 12px;
  border-top: 1px solid var(--border-color);
  background-color: white;
`;

const ChatInput = styled.input`
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  margin-right: 8px;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: var(--primary-color);
  }
`;

const SendButton = styled(Button)`
  border-radius: 20px;
`;

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatContainerProps {
  title?: string;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ title = '聊天' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '您好，我是您的需求澄清助手。请告诉我您的需求，我会帮助您进行分析和澄清。',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };
  
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isUser: true,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    
    setTimeout(() => {
      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '我已收到您的消息，正在处理中...',
        isUser: false,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, systemMessage]);
    }, 1000);
  };
  
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };
  
  return (
    <Card title={title}>
      <ChatWrapper>
        <ChatMessages>
          {messages.map((message) => (
            <MessageBubble key={message.id} isUser={message.isUser}>
              {message.text}
            </MessageBubble>
          ))}
          <div ref={messagesEndRef} />
        </ChatMessages>
        
        <ChatInputContainer>
          <ChatInput
            type="text"
            placeholder="输入消息..."
            value={inputValue}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
          />
          <SendButton onClick={handleSendMessage} disabled={!inputValue.trim()}>
            发送
          </SendButton>
        </ChatInputContainer>
      </ChatWrapper>
    </Card>
  );
};

export default ChatContainer;
