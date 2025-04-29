import React from 'react';
import styled from 'styled-components';
import Card from './common/Card';
import Button from './common/Button';
import { useGlobalStore } from '../store/globalStore';
import { Requirement, Module } from '../types';

const DetailPanelContainer = styled.div`
  width: 320px;
  border-left: 1px solid var(--border-color);
  background-color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
`;

const DetailHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  font-weight: bold;
  background-color: var(--secondary-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const DetailContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
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
  cursor: pointer;
  
  &:hover {
    background-color: var(--primary-color);
    color: white;
  }
`;

const RelatedItemsList = styled.div`
  margin-top: 8px;
`;

const RelatedItem = styled.div`
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  
  &:hover {
    background-color: var(--secondary-color);
  }
`;

interface DetailPanelProps {
  selectedType?: 'requirement' | 'module';
  selectedId?: string;
  onSelectItem: (type: 'requirement' | 'module', id: string) => void;
}

const DetailPanel: React.FC<DetailPanelProps> = ({ 
  selectedType, 
  selectedId,
  onSelectItem
}) => {
  const { state, getRelatedModules, getRelatedRequirements, getDeepReasoningResults } = useGlobalStore();
  const [relatedItems, setRelatedItems] = React.useState<Requirement[] | Module[]>([]);
  const [reasoningResult, setReasoningResult] = React.useState<string>('');
  const [isLoadingRelated, setIsLoadingRelated] = React.useState<boolean>(false);
  const [isLoadingReasoning, setIsLoadingReasoning] = React.useState<boolean>(false);
  
  const selectedItem = React.useMemo(() => {
    if (!selectedType || !selectedId) return null;
    
    if (selectedType === 'requirement') {
      return state.requirements.find(req => req.id === selectedId);
    } else {
      return state.modules.find(mod => mod.id === selectedId);
    }
  }, [selectedType, selectedId, state.requirements, state.modules]);
  
  React.useEffect(() => {
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
  
  const handleGetDeepReasoning = async () => {
    if (!selectedId || selectedType !== 'module') return;
    
    setIsLoadingReasoning(true);
    try {
      const result = await getDeepReasoningResults(selectedId);
      setReasoningResult(result);
    } catch (error) {
      console.error('Failed to get deep reasoning results:', error);
    } finally {
      setIsLoadingReasoning(false);
    }
  };
  
  const handleRelatedItemClick = (type: 'requirement' | 'module', id: string) => {
    onSelectItem(type, id);
  };
  
  if (!selectedItem) {
    return (
      <DetailPanelContainer>
        <DetailHeader>详情面板</DetailHeader>
        <DetailContent>
          <p>请选择一个需求或模块查看详情</p>
        </DetailContent>
      </DetailPanelContainer>
    );
  }
  
  return (
    <DetailPanelContainer>
      <DetailHeader>
        {selectedType === 'requirement' ? '需求详情' : '模块详情'}
      </DetailHeader>
      <DetailContent>
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
            
            <DetailSection>
              <Button 
                onClick={handleGetDeepReasoning}
                disabled={isLoadingReasoning}
              >
                {isLoadingReasoning ? '加载中...' : '获取深度推理结果'}
              </Button>
              
              {reasoningResult && (
                <Card title="深度推理结果" className="mt-3">
                  <SectionContent>
                    {reasoningResult}
                  </SectionContent>
                </Card>
              )}
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
            <RelatedItemsList>
              {relatedItems.map((item) => (
                <RelatedItem 
                  key={item.id}
                  onClick={() => handleRelatedItemClick(
                    selectedType === 'requirement' ? 'module' : 'requirement',
                    item.id
                  )}
                >
                  {item.name}
                </RelatedItem>
              ))}
            </RelatedItemsList>
          )}
        </DetailSection>
      </DetailContent>
    </DetailPanelContainer>
  );
};

export default DetailPanel;
