import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useGlobalStore } from '../store/globalStore';
import Button from './common/Button';
import Card from './common/Card';
import Loading from './common/Loading';
import ProjectSummary from './ProjectSummary';
import { Module, Requirement } from '../types';

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

const DetailSection = styled.div`
  margin-bottom: 16px;
`;

const SectionTitle = styled.h4`
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--light-text);
`;

const SectionContent = styled.div`
  font-size: 14px;
  line-height: 1.5;
`;

const TagList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
`;

const Tag = styled.span`
  background-color: var(--secondary-color);
  color: var(--primary-color);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
`;

interface MainContentProps {
  selectedType?: 'requirement' | 'module';
  selectedId?: string;
  onSelectItem: (type: 'requirement' | 'module', id: string) => void;
  version?: string;
}

const MainContent: React.FC<MainContentProps> = ({
  selectedType,
  selectedId,
  onSelectItem,
  version = 'react-frontend'
}) => {
  const { state, isLoading, error, startClarifier, fetchGlobalState, checkDependencies, getRelatedModules, getRelatedRequirements } = useGlobalStore();
  const [relatedItems, setRelatedItems] = useState<Requirement[] | Module[]>([]);
  const [isLoadingRelated, setIsLoadingRelated] = useState<boolean>(false);
  
  useEffect(() => {
    const loadRelatedItems = async () => {
      if (!selectedType || !selectedId) return;
      
      setIsLoadingRelated(true);
      try {
        if (selectedType === 'requirement') {
          const modules = await getRelatedModules(selectedId);
          setRelatedItems(modules);
        } else {
          const requirements = await getRelatedRequirements(selectedId);
          setRelatedItems(requirements);
        }
      } catch (error) {
        console.error('Failed to load related items:', error);
      } finally {
        setIsLoadingRelated(false);
      }
    };
    
    loadRelatedItems();
  }, [selectedType, selectedId, getRelatedModules, getRelatedRequirements]);
  
  const selectedItem = React.useMemo(() => {
    if (!selectedType || !selectedId) return null;
    
    if (selectedType === 'requirement') {
      return state.requirements.find(req => req.id === selectedId);
    } else {
      return state.modules.find(mod => mod.id === selectedId);
    }
  }, [selectedType, selectedId, state.requirements, state.modules]);
  
  const handleStartClarifier = () => {
    startClarifier();
  };
  
  const handleRefreshState = () => {
    fetchGlobalState();
  };
  
  const handleCheckDependencies = () => {
    checkDependencies();
  };
  
  const handleRelatedItemClick = (type: 'requirement' | 'module', id: string) => {
    onSelectItem(type, id);
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
      
      {/* 如果有选中的项目，则显示详情 */}
      {selectedItem ? (
        <Card title={selectedType === 'requirement' ? '需求详情' : '模块详情'}>
          <DetailSection>
            <SectionTitle>名称</SectionTitle>
            <SectionContent>{selectedItem.name}</SectionContent>
          </DetailSection>
          
          <DetailSection>
            <SectionTitle>描述</SectionTitle>
            <SectionContent>{selectedItem.description}</SectionContent>
          </DetailSection>
          
          {selectedType === 'requirement' && (
            <>
              <DetailSection>
                <SectionTitle>优先级</SectionTitle>
                <SectionContent>
                  {(selectedItem as Requirement).priority}
                </SectionContent>
              </DetailSection>
              
              <DetailSection>
                <SectionTitle>状态</SectionTitle>
                <SectionContent>
                  {(selectedItem as Requirement).status}
                </SectionContent>
              </DetailSection>
            </>
          )}
          
          {selectedType === 'module' && (
            <>
              <DetailSection>
                <SectionTitle>职责</SectionTitle>
                <SectionContent>
                  <ul>
                    {(selectedItem as Module).responsibilities.map((resp, index) => (
                      <li key={index}>{resp}</li>
                    ))}
                  </ul>
                </SectionContent>
              </DetailSection>
              
              <DetailSection>
                <SectionTitle>依赖</SectionTitle>
                <TagList>
                  {(selectedItem as Module).dependencies.length === 0 ? (
                    <span>无依赖</span>
                  ) : (
                    (selectedItem as Module).dependencies.map((dep, index) => (
                      <Tag key={index}>{dep}</Tag>
                    ))
                  )}
                </TagList>
              </DetailSection>
              
              <DetailSection>
                <SectionTitle>层级</SectionTitle>
                <SectionContent>
                  {(selectedItem as Module).layer}
                </SectionContent>
              </DetailSection>
              
              <DetailSection>
                <SectionTitle>领域</SectionTitle>
                <SectionContent>
                  {(selectedItem as Module).domain}
                </SectionContent>
              </DetailSection>
            </>
          )}
          
          <DetailSection>
            <SectionTitle>
              {selectedType === 'requirement' ? '相关模块' : '相关需求'}
            </SectionTitle>
            
            {isLoadingRelated ? (
              <p>加载中...</p>
            ) : relatedItems.length === 0 ? (
              <p>无相关{selectedType === 'requirement' ? '模块' : '需求'}</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
                {relatedItems.map((item) => (
                  <div 
                    key={item.id}
                    onClick={() => handleRelatedItemClick(
                      selectedType === 'requirement' ? 'module' : 'requirement',
                      item.id
                    )}
                    style={{
                      padding: '8px',
                      border: '1px solid var(--border-color)',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    {item.name}
                  </div>
                ))}
              </div>
            )}
          </DetailSection>
        </Card>
      ) : (
        <>
          <div style={{ fontSize: '12px', color: '#666', position: 'absolute', right: '10px', top: '10px' }}>{version}</div>
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
        </>
      )}
    </MainContentContainer>
  );
};

export default MainContent;
