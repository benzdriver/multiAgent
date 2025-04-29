import React from 'react';
import styled, { keyframes } from 'styled-components';

interface LoadingProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  fullScreen?: boolean;
  text?: string;
}

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const LoadingContainer = styled.div<{ fullScreen: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  ${props => props.fullScreen ? `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.8);
    z-index: 1000;
  ` : ''}
`;

const Spinner = styled.div<{ size: string; color: string }>`
  border: ${props => props.size === 'small' ? '2px' : props.size === 'medium' ? '3px' : '4px'} solid rgba(0, 0, 0, 0.1);
  border-top: ${props => props.size === 'small' ? '2px' : props.size === 'medium' ? '3px' : '4px'} solid ${props => props.color};
  border-radius: 50%;
  width: ${props => props.size === 'small' ? '16px' : props.size === 'medium' ? '32px' : '48px'};
  height: ${props => props.size === 'small' ? '16px' : props.size === 'medium' ? '32px' : '48px'};
  animation: ${spin} 1s linear infinite;
`;

const LoadingText = styled.div`
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-color);
`;

const Loading: React.FC<LoadingProps> = ({
  size = 'medium',
  color = 'var(--primary-color)',
  fullScreen = false,
  text,
}) => {
  return (
    <LoadingContainer fullScreen={fullScreen}>
      <Spinner size={size} color={color} />
      {text && <LoadingText>{text}</LoadingText>}
    </LoadingContainer>
  );
};

export default Loading;
