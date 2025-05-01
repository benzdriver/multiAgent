import React from 'react';
import styled from 'styled-components';
import Card from './common/Card';
import Button from './common/Button';
import { useGlobalStore } from '../store/globalStore';
import { Requirement, Module } from '../types';
import ModuleSummaryTest from './ModuleSummaryTest';

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
  const { state, getRelatedModules, getRelatedRequirements, deepReasoning } = useGlobalStore();
  const [relatedItems, setRelatedItems] = React.useState<Requirement[] | Module[]>([]);
  const [reasoningResult, setReasoningResult] = React.useState<string>('');
  const [isLoadingRelated, setIsLoadingRelated] = React.useState<boolean>(false);
  const [isLoadingReasoning, setIsLoadingReasoning] = React.useState<boolean>(false);
  const [fullSummary, setFullSummary] = React.useState<any>(null);
  
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
  
  React.useEffect(() => {
    const fetchFullSummary = async () => {
      if (!selectedType || selectedType !== 'module' || !selectedId) {
        console.log('不获取模块摘要: 未选择模块或选择类型不是模块', { selectedType, selectedId });
        setFullSummary(null);
        return;
      }
      
      console.log('尝试获取模块摘要', { selectedType, selectedId });
      console.log('当前模块列表', state.modules);
      
      const selectedModule = state.modules.find(mod => mod.id === selectedId);
      if (!selectedModule || !selectedModule.name) {
        console.log('未找到选中的模块或模块名称为空', { selectedId });
        return;
      }
      
      console.log('找到选中的模块', { moduleName: selectedModule.name });
      
      try {
        const moduleName = selectedModule.name;
        const url = `/api/module_summary/${encodeURIComponent(moduleName)}`;
        console.log('请求模块摘要API', { url });
        
        const response = await fetch(url);
        console.log('模块摘要API响应', { status: response.status });
        
        if (response.ok) {
          const data = await response.json();
          console.log('获取到模块摘要数据', data);
          console.log('设置fullSummary状态', data);
          setFullSummary(data);
        } else {
          const errorText = await response.text();
          console.error('模块摘要API错误', { status: response.status, error: errorText });
          
          const altModuleName = selectedModule.name
            .split(' ').join('_')  // 替换空格为下划线
            .replace(/[^\w\s\-_]/g, ''); // 移除非字母数字字符
          
          if (altModuleName !== moduleName) {
            console.log('尝试使用替代名称获取摘要', { altModuleName });
            const altUrl = `/api/module_summary/${encodeURIComponent(altModuleName)}`;
            const altResponse = await fetch(altUrl);
            
            if (altResponse.ok) {
              const data = await altResponse.json();
              console.log('使用替代名称获取到数据', data);
              setFullSummary(data);
            } else {
              console.error('替代名称也无法获取模块摘要');
              
              const moduleWithSafeName = selectedModule as any;
              if (moduleWithSafeName.safe_module_name) {
                console.log('尝试使用safe_module_name获取摘要', { safe_module_name: moduleWithSafeName.safe_module_name });
                const safeUrl = `/api/module_summary/${encodeURIComponent(moduleWithSafeName.safe_module_name)}`;
                const safeResponse = await fetch(safeUrl);
                
                if (safeResponse.ok) {
                  const data = await safeResponse.json();
                  console.log('使用safe_module_name获取到数据', data);
                  setFullSummary(data);
                } else {
                  console.error('所有尝试都失败，无法获取模块摘要');
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('获取模块摘要失败:', error);
      }
    };
    
    fetchFullSummary();
  }, [selectedType, selectedId, state.modules]);
  
  const handleGetDeepReasoning = async () => {
    if (!selectedId || selectedType !== 'module') return;
    
    setIsLoadingReasoning(true);
    try {
      await deepReasoning();
      setReasoningResult(`已为模块 ${selectedItem?.name} 生成深度推理结果，请在全局状态中查看。`);
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
            
            {selectedType === 'module' && (
              <DetailSection>
                <SectionTitle>模块完整摘要</SectionTitle>
                <SectionContent>
                  {fullSummary ? (
                    <pre style={{ 
                      background: '#f5f5f5', 
                      padding: '10px', 
                      borderRadius: '4px',
                      overflow: 'auto',
                      maxHeight: '300px',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {JSON.stringify(fullSummary, null, 2)}
                    </pre>
                  ) : (
                    <div>
                      <p>加载模块摘要中...</p>
                      <button 
                        onClick={() => {
                          const selectedModule = state.modules.find(mod => mod.id === selectedId);
                          if (selectedModule && selectedModule.name) {
                            console.log('手动刷新模块摘要');
                            
                            const url = `/api/module_summary/${encodeURIComponent(selectedModule.name)}`;
                            console.log('尝试原始名称', { url });
                            
                            fetch(url)
                              .then(response => {
                                if (response.ok) {
                                  return response.json();
                                }
                                
                                const altModuleName = selectedModule.name
                                  .split(' ').join('_')
                                  .replace(/[^\w\s\-_]/g, '');
                                
                                if (altModuleName !== selectedModule.name) {
                                  console.log('尝试替代名称', { altModuleName });
                                  const altUrl = `/api/module_summary/${encodeURIComponent(altModuleName)}`;
                                  return fetch(altUrl).then(altResponse => {
                                    if (altResponse.ok) {
                                      return altResponse.json();
                                    }
                                    
                                    const moduleWithSafeName = selectedModule as any;
                                    if (moduleWithSafeName.safe_module_name) {
                                      console.log('尝试safe_module_name', { safe_module_name: moduleWithSafeName.safe_module_name });
                                      const safeUrl = `/api/module_summary/${encodeURIComponent(moduleWithSafeName.safe_module_name)}`;
                                      return fetch(safeUrl).then(safeResponse => {
                                        if (safeResponse.ok) {
                                          return safeResponse.json();
                                        }
                                        throw new Error('所有尝试都失败');
                                      });
                                    }
                                    throw new Error('获取模块摘要失败');
                                  });
                                }
                                throw new Error('获取模块摘要失败');
                              })
                              .then(data => {
                                console.log('获取到模块摘要数据', data);
                                setFullSummary(data);
                              })
                              .catch(error => {
                                console.error('获取模块摘要失败:', error);
                                alert('获取模块摘要失败，请检查控制台日志');
                              });
                          }
                        }}
                        style={{
                          padding: '5px 10px',
                          background: '#4a6bff',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        刷新模块摘要
                      </button>
                    </div>
                  )}
                </SectionContent>
              </DetailSection>
            )}
            
            {selectedType === 'module' && selectedItem && (
              <DetailSection>
                <SectionTitle>模块摘要测试组件</SectionTitle>
                <SectionContent>
                  <ModuleSummaryTest moduleName={(selectedItem as Module).name} />
                </SectionContent>
              </DetailSection>
            )}
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
