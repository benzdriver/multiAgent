import React from 'react';
import styled from 'styled-components';
import Card from './common/Card';
import { useGlobalStore } from '../store/globalStore';

const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
`;

const StatCard = styled(Card)`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-color);
  margin: 8px 0;
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: var(--light-text);
`;

const TechStackSection = styled.div`
  margin-top: 20px;
`;

const TechStackGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
`;

const TechStackItem = styled.div`
  background-color: white;
  border-radius: 4px;
  padding: 12px;
  border: 1px solid var(--border-color);
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const TechName = styled.div`
  font-weight: 600;
  margin-bottom: 4px;
`;

const TechCategory = styled.div`
  font-size: 12px;
  color: var(--light-text);
  margin-bottom: 8px;
`;

const TechDescription = styled.div`
  font-size: 13px;
  line-height: 1.4;
`;

const ProjectSummary: React.FC = () => {
  const { state } = useGlobalStore();
  
  return (
    <Card title="项目概览">
      <SummaryGrid>
        <StatCard>
          <StatValue>{state.requirements.length}</StatValue>
          <StatLabel>需求总数</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue>{state.modules.length}</StatValue>
          <StatLabel>模块总数</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue>{state.validationIssues.length}</StatValue>
          <StatLabel>验证问题</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue>{state.circularDependencies.length}</StatValue>
          <StatLabel>循环依赖</StatLabel>
        </StatCard>
      </SummaryGrid>
      
      {state.techStack.length > 0 && (
        <TechStackSection>
          <h3>技术栈</h3>
          <TechStackGrid>
            {state.techStack.map((tech) => (
              <TechStackItem key={tech.id}>
                <TechName>{tech.name}</TechName>
                <TechCategory>{tech.category}</TechCategory>
                <TechDescription>{tech.description}</TechDescription>
              </TechStackItem>
            ))}
          </TechStackGrid>
        </TechStackSection>
      )}
    </Card>
  );
};

export default ProjectSummary;
