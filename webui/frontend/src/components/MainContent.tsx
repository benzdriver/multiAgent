import React from 'react';
import styled from 'styled-components';
import { useGlobalStore } from '../store/globalStore';
import Button from './common/Button';
import Card from './common/Card';
import Loading from './common/Loading';
import ProjectSummary from './ProjectSummary';

const MainContentContainer = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f9f9f9;
`;

const ActionBar = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
`;

const ValidationIssueCard = styled(Card)`
  border-left: 3px solid var(--warning-color);
`;

const CircularDependencyCard = styled(Card)`
  border-left: 3px solid var(--danger-color);
`;

const MainContent: React.FC = () => {
  const { state, isLoading, error, startClarifier, fetchGlobalState, checkDependencies } = useGlobalStore();
  
  const handleStartClarifier = () => {
    startClarifier();
  };
  
  const handleRefreshState = () => {
    fetchGlobalState();
  };
  
  const handleCheckDependencies = () => {
    checkDependencies();
  };
  
  return (
    <MainContentContainer>
      {isLoading && <Loading fullScreen text="加载中..." />}
      
      <ActionBar>
        <Button onClick={handleStartClarifier} disabled={false}>
          启动澄清器
        </Button>
        <Button onClick={handleRefreshState} disabled={isLoading} type="secondary">
          刷新状态
        </Button>
        <Button onClick={handleCheckDependencies} disabled={isLoading} type="secondary">
          检查依赖关系
        </Button>
      </ActionBar>
      
      {error && (
        <Card title="错误">
          <div style={{ color: 'var(--danger-color)' }}>{error}</div>
        </Card>
      )}
      
      <ProjectSummary />
      
      {state.validationIssues.length > 0 && (
        <ValidationIssueCard title="验证问题">
          {state.validationIssues.map((issue) => (
            <div key={issue.id} style={{ marginBottom: '12px' }}>
              <h4>{issue.type}</h4>
              <p>{issue.description}</p>
              <div>
                <strong>相关项目: </strong>
                {issue.relatedItems.join(', ')}
              </div>
              <div>
                <strong>严重程度: </strong>
                {issue.severity}
              </div>
            </div>
          ))}
        </ValidationIssueCard>
      )}
      
      {state.circularDependencies.length > 0 && (
        <CircularDependencyCard title="循环依赖">
          {state.circularDependencies.map((dependency) => (
            <div key={dependency.id} style={{ marginBottom: '12px' }}>
              <p>{dependency.description}</p>
              <div>
                <strong>模块: </strong>
                {dependency.modules.join(' → ')}
              </div>
            </div>
          ))}
        </CircularDependencyCard>
      )}
    </MainContentContainer>
  );
};

export default MainContent;
