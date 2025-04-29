import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import Button from './common/Button';
import Card from './common/Card';

const UploadContainer = styled.div`
  margin-bottom: 20px;
`;

const DropZone = styled.div<{ isDragging: boolean }>`
  border: 2px dashed ${props => props.isDragging ? 'var(--primary-color)' : 'var(--border-color)'};
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  background-color: ${props => props.isDragging ? 'var(--secondary-color)' : 'white'};
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 16px;
  
  &:hover {
    background-color: var(--secondary-color);
    border-color: var(--primary-color);
  }
`;

const UploadIcon = styled.div`
  font-size: 24px;
  margin-bottom: 10px;
  color: var(--primary-color);
`;

const UploadText = styled.div`
  font-size: 14px;
  color: var(--light-text);
  margin-bottom: 8px;
`;

const FileInput = styled.input`
  display: none;
`;

const FileList = styled.div`
  margin-top: 16px;
`;

const FileItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 8px;
  background-color: white;
`;

const FileName = styled.div`
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
`;

const FileSize = styled.div`
  font-size: 12px;
  color: var(--light-text);
  margin: 0 12px;
`;

const RemoveButton = styled.button`
  background: none;
  border: none;
  color: var(--danger-color);
  cursor: pointer;
  font-size: 16px;
  padding: 0 8px;
  
  &:hover {
    opacity: 0.8;
  }
`;

interface FileInfo {
  id: string;
  file: File;
  progress: number;
}

interface FileUploadProps {
  title?: string;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in MB
  onFilesSelected?: (files: File[]) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  title = '文件上传',
  accept = '.txt,.md,.pdf,.doc,.docx',
  multiple = true,
  maxSize = 10, // 10MB
  onFilesSelected,
}) => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
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
  
  const validateFiles = (fileList: FileList): File[] => {
    const validFiles: File[] = [];
    const maxSizeBytes = maxSize * 1024 * 1024;
    
    Array.from(fileList).forEach(file => {
      if (file.size > maxSizeBytes) {
        setError(`文件 "${file.name}" 超过最大大小限制 (${maxSize}MB)`);
        return;
      }
      
      validFiles.push(file);
    });
    
    return validFiles;
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setError(null);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const validFiles = validateFiles(e.dataTransfer.files);
      handleFiles(validFiles);
    }
  };
  
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    
    if (e.target.files && e.target.files.length > 0) {
      const validFiles = validateFiles(e.target.files);
      handleFiles(validFiles);
    }
  };
  
  const handleFiles = (newFiles: File[]) => {
    if (newFiles.length === 0) return;
    
    const newFileInfos: FileInfo[] = newFiles.map(file => ({
      id: `${file.name}-${Date.now()}`,
      file,
      progress: 0,
    }));
    
    setFiles(prev => [...prev, ...newFileInfos]);
    
    if (onFilesSelected) {
      onFilesSelected(newFiles);
    }
    
    newFileInfos.forEach(fileInfo => {
      simulateUploadProgress(fileInfo.id);
    });
  };
  
  const simulateUploadProgress = (fileId: string) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      
      setFiles(prev => 
        prev.map(file => 
          file.id === fileId 
            ? { ...file, progress: Math.min(progress, 100) } 
            : file
        )
      );
      
      if (progress >= 100) {
        clearInterval(interval);
      }
    }, 300);
  };
  
  const handleRemoveFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId));
  };
  
  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  return (
    <Card title={title}>
      <UploadContainer>
        <DropZone
          isDragging={isDragging}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
        >
          <UploadIcon>📁</UploadIcon>
          <UploadText>拖拽文件到此处或点击浏览</UploadText>
          <UploadText>支持的文件类型: {accept}</UploadText>
          <Button type="secondary">浏览文件</Button>
          <FileInput
            type="file"
            ref={fileInputRef}
            accept={accept}
            multiple={multiple}
            onChange={handleFileInputChange}
          />
        </DropZone>
        
        {error && (
          <div style={{ color: 'var(--danger-color)', marginBottom: '16px' }}>
            {error}
          </div>
        )}
        
        {files.length > 0 && (
          <FileList>
            <h4>已选文件</h4>
            {files.map(fileInfo => (
              <FileItem key={fileInfo.id}>
                <FileName>{fileInfo.file.name}</FileName>
                <FileSize>{formatFileSize(fileInfo.file.size)}</FileSize>
                <RemoveButton onClick={() => handleRemoveFile(fileInfo.id)}>
                  ×
                </RemoveButton>
              </FileItem>
            ))}
          </FileList>
        )}
      </UploadContainer>
    </Card>
  );
};

export default FileUpload;
