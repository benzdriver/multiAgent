import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useGlobalStore } from '../store/globalStore';
import { Module, Requirement } from '../types';

const SidebarContainer = styled.div`
  width: 280px;
  border-right: 1px solid var(--border-color);
  background-color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
`;

const SidebarHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--secondary-color);
`;

const ProjectTitle = styled.h2`
  font-size: 16px;
  margin: 0 0 12px 0;
  font-weight: bold;
  color: var(--text-color);
`;

const ProjectOverview = styled.div`
  margin-top: 8px;
  font-size: 14px;
`;

const OverviewItem = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
`;

const Label = styled.span`
  color: var(--light-text);
`;

const Value = styled.span`
  font-weight: 500;
`;

const TechStack = styled.div`
  margin-top: 8px;
`;

const TechTag = styled.span`
  display: inline-block;
  background-color: white;
  color: var(--primary-color);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 4px;
  margin-bottom: 4px;
  border: 1px solid var(--primary-color);
`;

const RequirementSelector = styled.div`
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
`;

const SelectLabel = styled.label`
  display: block;
  font-size: 14px;
  margin-bottom: 8px;
  color: var(--text-color);
  font-weight: 500;
`;

const Select = styled.select`
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  
  &:focus {
    outline: none;
    border-color: var(--primary-color);
  }
`;

const ModuleList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px;
`;

const LayerGroup = styled.div`
  margin-bottom: 16px;
`;

const LayerTitleContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
`;

const LayerTitle = styled.h3`
  font-size: 14px;
  margin: 0;
  color: var(--light-text);
  font-weight: bold;
`;

const CollapseIcon = styled.span<{ expanded?: boolean }>`
  font-size: 16px;
  color: var(--light-text);
  transition: transform 0.2s ease;
  transform: ${props => props.expanded ? 'rotate(0deg)' : 'rotate(-90deg)'};
  display: inline-block;
`;

const ModuleContainer = styled.div<{ expanded?: boolean }>`
  max-height: ${props => props.expanded ? '1000px' : '0'};
  overflow: hidden;
  transition: max-height 0.3s ease;
`;

const SidebarItem = styled.div<{ active?: boolean }>`
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  background-color: ${props => props.active ? 'var(--secondary-color)' : 'transparent'};
  border-left: ${props => props.active ? '3px solid var(--primary-color)' : 'none'};
  padding-left: ${props => props.active ? '13px' : '16px'};
  margin-bottom: 4px;
  border-radius: 4px;
  
  &:hover {
    background-color: var(--secondary-color);
  }
`;

const EmptyState = styled.div`
  padding: 20px;
  text-align: center;
  color: var(--light-text);
`;

interface SidebarProps {
  onSelectItem: (type: 'requirement' | 'module', id: string) => void;
  selectedType?: 'requirement' | 'module';
  selectedId?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  onSelectItem, 
  selectedType = 'requirement', 
  selectedId 
}) => {
  const { state } = useGlobalStore();
  const [selectedRequirement, setSelectedRequirement] = useState<string>('');
  const [filteredModules, setFilteredModules] = useState<Module[]>([]);
  const [expandedLayers, setExpandedLayers] = useState<Record<string, boolean>>({});
  
  const groupModulesByLayer = (modules: Module[]) => {
    const groups: Record<string, Module[]> = {};
    
    modules.forEach(module => {
      const layer = module.layer || '未分类';
      if (!groups[layer]) {
        groups[layer] = [];
      }
      groups[layer].push(module);
    });
    
    return groups;
  };
  
  useEffect(() => {
    const layers = Object.keys(groupModulesByLayer(state.modules));
    const initialExpandedState: Record<string, boolean> = {};
    
    layers.forEach(layer => {
      initialExpandedState[layer] = true;
    });
    
    setExpandedLayers(initialExpandedState);
  }, [state.modules]);
  
  useEffect(() => {
    if (selectedRequirement) {
      const requirement = state.requirements.find(req => req.id === selectedRequirement);
      if (requirement) {
        const related = state.modules.filter(mod => {
          const nameMatch = mod.name.toLowerCase().includes(requirement.name.toLowerCase());
          
          const descMatch = requirement.description.toLowerCase().includes(mod.name.toLowerCase());
          
          const respMatch = mod.responsibilities.some(resp => 
            resp.toLowerCase().includes(requirement.name.toLowerCase()) ||
            requirement.description.toLowerCase().includes(resp.toLowerCase())
          );
          
          return nameMatch || descMatch || respMatch;
        });
        
        setFilteredModules(related);
        
        const relatedLayers = new Set(related.map(mod => mod.layer || '未分类'));
        const newExpandedState = {...expandedLayers};
        
        relatedLayers.forEach(layer => {
          newExpandedState[layer] = true;
        });
        
        setExpandedLayers(newExpandedState);
      }
    } else {
      setFilteredModules(state.modules);
    }
  }, [selectedRequirement, state.requirements, state.modules]);
  
  const handleRequirementChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const reqId = e.target.value;
    setSelectedRequirement(reqId);
    
    if (reqId) {
      onSelectItem('requirement', reqId);
    }
  };
  
  const handleModuleClick = (moduleId: string) => {
    onSelectItem('module', moduleId);
  };
  
  const toggleLayerExpand = (layer: string) => {
    setExpandedLayers(prev => ({
      ...prev,
      [layer]: !prev[layer]
    }));
  };
  
  const projectStats = {
    requirementsCount: state.requirements.length,
    modulesCount: state.modules.length,
    issuesCount: state.validationIssues.length,
    techStack: ['React', 'FastAPI', 'Python', 'TypeScript']
  };
  
  const modulesByLayer = groupModulesByLayer(filteredModules);
  
  return (
    <SidebarContainer>
      <SidebarHeader>
        <ProjectTitle>项目概览</ProjectTitle>
        <ProjectOverview>
          <OverviewItem>
            <Label>需求数量:</Label>
            <Value>{projectStats.requirementsCount}</Value>
          </OverviewItem>
          <OverviewItem>
            <Label>模块数量:</Label>
            <Value>{projectStats.modulesCount}</Value>
          </OverviewItem>
          <OverviewItem>
            <Label>问题数量:</Label>
            <Value>{projectStats.issuesCount}</Value>
          </OverviewItem>
          <TechStack>
            <Label>技术栈:</Label>
            <div style={{ marginTop: '4px' }}>
              {projectStats.techStack.map((tech, index) => (
                <TechTag key={index}>{tech}</TechTag>
              ))}
            </div>
          </TechStack>
        </ProjectOverview>
      </SidebarHeader>
      
      <RequirementSelector>
        <SelectLabel>选择需求</SelectLabel>
        <Select 
          value={selectedRequirement} 
          onChange={handleRequirementChange}
        >
          <option value="">全部需求</option>
          {state.requirements.map(req => (
            <option key={req.id} value={req.id}>
              {req.name}
            </option>
          ))}
        </Select>
      </RequirementSelector>
      
      <ModuleList>
        {Object.keys(modulesByLayer).length > 0 ? (
          Object.entries(modulesByLayer).map(([layer, modules]) => (
            <LayerGroup key={layer}>
              <LayerTitleContainer onClick={() => toggleLayerExpand(layer)}>
                <LayerTitle>{layer}</LayerTitle>
                <CollapseIcon expanded={expandedLayers[layer]}>▼</CollapseIcon>
              </LayerTitleContainer>
              
              <ModuleContainer expanded={expandedLayers[layer]}>
                {modules.map(module => (
                  <SidebarItem
                    key={module.id}
                    active={selectedType === 'module' && selectedId === module.id}
                    onClick={() => handleModuleClick(module.id)}
                  >
                    {module.name}
                  </SidebarItem>
                ))}
              </ModuleContainer>
            </LayerGroup>
          ))
        ) : (
          <EmptyState>
            {selectedRequirement ? '该需求暂无相关模块' : '暂无模块'}
          </EmptyState>
        )}
      </ModuleList>
    </SidebarContainer>
  );
};

export default Sidebar;
