import React from 'react';
import styled from 'styled-components';
import { useGlobalStore } from '../store/globalStore';
import { Requirement, Module } from '../types';

const SidebarContainer = styled.div`
  width: 240px;
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
  font-weight: bold;
  background-color: var(--secondary-color);
`;

const SidebarContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
`;

const SidebarItem = styled.div<{ active?: boolean }>`
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  background-color: ${props => props.active ? 'var(--secondary-color)' : 'transparent'};
  border-left: ${props => props.active ? '3px solid var(--primary-color)' : 'none'};
  padding-left: ${props => props.active ? '13px' : '16px'};
  
  &:hover {
    background-color: var(--secondary-color);
  }
`;

const TabContainer = styled.div`
  display: flex;
  border-bottom: 1px solid var(--border-color);
`;

const Tab = styled.div<{ active: boolean }>`
  padding: 10px 16px;
  cursor: pointer;
  flex: 1;
  text-align: center;
  background-color: ${props => props.active ? 'var(--secondary-color)' : 'transparent'};
  border-bottom: ${props => props.active ? '2px solid var(--primary-color)' : 'none'};
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  
  &:hover {
    background-color: var(--secondary-color);
  }
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
  const [activeTab, setActiveTab] = React.useState<'requirements' | 'modules'>('requirements');
  
  const handleTabChange = (tab: 'requirements' | 'modules') => {
    setActiveTab(tab);
  };
  
  const handleItemClick = (type: 'requirement' | 'module', id: string) => {
    onSelectItem(type, id);
  };
  
  return (
    <SidebarContainer>
      <SidebarHeader>项目导航</SidebarHeader>
      <TabContainer>
        <Tab 
          active={activeTab === 'requirements'} 
          onClick={() => handleTabChange('requirements')}
        >
          需求
        </Tab>
        <Tab 
          active={activeTab === 'modules'} 
          onClick={() => handleTabChange('modules')}
        >
          模块
        </Tab>
      </TabContainer>
      <SidebarContent>
        {activeTab === 'requirements' ? (
          state.requirements.length === 0 ? (
            <SidebarItem>暂无需求</SidebarItem>
          ) : (
            state.requirements.map((requirement: Requirement) => (
              <SidebarItem
                key={requirement.id}
                active={selectedType === 'requirement' && selectedId === requirement.id}
                onClick={() => handleItemClick('requirement', requirement.id)}
              >
                {requirement.name}
              </SidebarItem>
            ))
          )
        ) : (
          state.modules.length === 0 ? (
            <SidebarItem>暂无模块</SidebarItem>
          ) : (
            state.modules.map((module: Module) => (
              <SidebarItem
                key={module.id}
                active={selectedType === 'module' && selectedId === module.id}
                onClick={() => handleItemClick('module', module.id)}
              >
                {module.name}
              </SidebarItem>
            ))
          )
        )}
      </SidebarContent>
    </SidebarContainer>
  );
};

export default Sidebar;
