import React from 'react';
import styled from 'styled-components';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'primary' | 'secondary' | 'danger' | 'success';
  disabled?: boolean;
  fullWidth?: boolean;
  className?: string;
}

const StyledButton = styled.button<{
  buttonType: 'primary' | 'secondary' | 'danger' | 'success';
  fullWidth: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  width: ${props => (props.fullWidth ? '100%' : 'auto')};
  
  ${props => {
    switch (props.buttonType) {
      case 'primary':
        return `
          background-color: var(--primary-color);
          color: white;
          border: 1px solid var(--primary-color);
          &:hover {
            background-color: #3a5bc7;
          }
        `;
      case 'secondary':
        return `
          background-color: white;
          color: var(--primary-color);
          border: 1px solid var(--primary-color);
          &:hover {
            background-color: var(--secondary-color);
          }
        `;
      case 'danger':
        return `
          background-color: var(--danger-color);
          color: white;
          border: 1px solid var(--danger-color);
          &:hover {
            background-color: #c82333;
          }
        `;
      case 'success':
        return `
          background-color: var(--success-color);
          color: white;
          border: 1px solid var(--success-color);
          &:hover {
            background-color: #218838;
          }
        `;
      default:
        return '';
    }
  }}
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    &:hover {
      opacity: 0.6;
    }
  }
`;

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  type = 'primary',
  disabled = false,
  fullWidth = false,
  className = '',
}) => {
  return (
    <StyledButton
      buttonType={type}
      fullWidth={fullWidth}
      onClick={onClick}
      disabled={disabled}
      className={className}
    >
      {children}
    </StyledButton>
  );
};

export default Button;
