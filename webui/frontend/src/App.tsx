import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import styled from 'styled-components';
import { useGlobalStore } from './store/globalStore';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent';
import DetailPanel from './components/DetailPanel';
import Loading from './components/common/Loading';
import ChatContainer from './components/ChatContainer';
import FileUpload from './components/FileUpload';

const queryClient = new QueryClient();

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
`;

const Header = styled.header`
  background-color: var(--primary-color);
  color: white;
  padding: 16px 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const HeaderTitle = styled.h1`
  margin: 0;
  font-size: 20px;
  font-weight: 600;
`;

const MainLayout = styled.main`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const ContentArea = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const BottomSection = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
  background-color: #f5f5f5;
  border-top: 1px solid var(--border-color);
`;

const AppContent: React.FC = () => {
  const { fetchGlobalState, isLoading } = useGlobalStore();
  const [selectedType, setSelectedType] = useState<'requirement' | 'module' | undefined>();
  const [selectedId, setSelectedId] = useState<string | undefined>();
  
  useEffect(() => {
    fetchGlobalState();
  }, [fetchGlobalState]);
  
  const handleSelectItem = (type: 'requirement' | 'module', id: string) => {
    setSelectedType(type);
    setSelectedId(id);
  };
  
  if (isLoading && !selectedId) {
    return <Loading fullScreen text="加载中..." />;
  }
  
  return (
    <AppContainer>
      <Header>
        <HeaderTitle>需求澄清与架构设计系统</HeaderTitle>
      </Header>
      <MainLayout>
        <Sidebar 
          onSelectItem={handleSelectItem}
          selectedType={selectedType}
          selectedId={selectedId}
        />
        <ContentArea>
          <MainContent 
            selectedType={selectedType}
            selectedId={selectedId}
            onSelectItem={handleSelectItem}
            version="react-frontend-v2"
          />
          <BottomSection>
            <ChatContainer title="需求澄清助手" />
            <FileUpload title="上传需求文档" />
          </BottomSection>
        </ContentArea>
        <DetailPanel 
          selectedType={selectedType}
          selectedId={selectedId}
          onSelectItem={handleSelectItem}
        />
      </MainLayout>
    </AppContainer>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
};

export default App;
