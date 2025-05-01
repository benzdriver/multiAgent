import React, { useState, useRef } from 'react';
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
  flex-direction: column;
  padding: 12px;
  border-top: 1px solid var(--border-color);
  background-color: white;
  position: relative;
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

const UploadIcon = styled.div`
  position: absolute;
  right: 70px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  color: var(--primary-color);
  cursor: pointer;
  
  &:hover {
    opacity: 0.8;
  }
`;

const FileInput = styled.input`
  display: none;
`;

const FilePreview = styled.div`
  padding: 8px 12px;
  background-color: #f0f0f0;
  border-radius: 8px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
`;

const InputRow = styled.div`
  display: flex;
  width: 100%;
`;

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  file?: {
    name: string;
    size: number;
    type: string;
  };
}

interface ChatContainerProps {
  title?: string;
  acceptFileUpload?: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ 
  title = '聊天', 
  acceptFileUpload = false 
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '您好，我是您的需求澄清助手。请告诉我您的需求，我会帮助您进行分析和澄清。您也可以直接拖拽文件到聊天框中上传。',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatWrapperRef = useRef<HTMLDivElement>(null);
  
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };
  
  const handleSendMessage = () => {
    if (!inputValue.trim() && !selectedFile) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue || (selectedFile ? `上传文件: ${selectedFile.name}` : ''),
      isUser: true,
      timestamp: new Date(),
      file: selectedFile ? {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type
      } : undefined
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setSelectedFile(null);
    
    setTimeout(() => {
      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: selectedFile 
          ? `我已收到您上传的文件 ${selectedFile.name}，正在处理中...` 
          : '我已收到您的消息，正在处理中...',
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
  
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };
  
  const handleRemoveFile = () => {
    setSelectedFile(null);
  };
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };
  
  return (
    <Card title={title}>
      <ChatWrapper 
        ref={chatWrapperRef}
        onDragEnter={acceptFileUpload ? handleDragEnter : undefined}
        onDragLeave={acceptFileUpload ? handleDragLeave : undefined}
        onDragOver={acceptFileUpload ? handleDragOver : undefined}
        onDrop={acceptFileUpload ? handleDrop : undefined}
        style={{ 
          border: isDragging ? '2px dashed var(--primary-color)' : '1px solid var(--border-color)',
          height: '500px' // 增大聊天框高度
        }}
      >
        <ChatMessages>
          {messages.map((message) => (
            <MessageBubble key={message.id} isUser={message.isUser}>
              {message.text}
              {message.file && (
                <div style={{ 
                  marginTop: '8px', 
                  padding: '4px 8px', 
                  backgroundColor: 'rgba(0,0,0,0.1)', 
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  📎 {message.file.name} ({formatFileSize(message.file.size)})
                </div>
              )}
            </MessageBubble>
          ))}
          <div ref={messagesEndRef} />
        </ChatMessages>
        
        <ChatInputContainer>
          {selectedFile && (
            <FilePreview>
              <span>📎 {selectedFile.name} ({formatFileSize(selectedFile.size)})</span>
              <span onClick={handleRemoveFile} style={{ cursor: 'pointer' }}>×</span>
            </FilePreview>
          )}
          
          <InputRow>
            <ChatInput
              type="text"
              placeholder={isDragging ? "释放鼠标上传文件..." : "输入消息或拖拽文件到此处..."}
              value={inputValue}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
            />
            
            {acceptFileUpload && (
              <>
                <UploadIcon onClick={handleUploadClick}>📎</UploadIcon>
                <FileInput
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".txt,.md,.pdf,.doc,.docx"
                />
              </>
            )}
            
            <SendButton onClick={handleSendMessage} disabled={!inputValue.trim() && !selectedFile}>
              发送
            </SendButton>
          </InputRow>
        </ChatInputContainer>
      </ChatWrapper>
    </Card>
  );
};

export default ChatContainer;
