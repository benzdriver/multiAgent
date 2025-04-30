import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

const TestContainer = styled.div`
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-top: 20px;
`;

const Button = styled.button`
  padding: 8px 16px;
  background-color: #4a6bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 10px;
`;

const Pre = styled.pre`
  background-color: #fff;
  padding: 10px;
  border-radius: 4px;
  overflow: auto;
  max-height: 300px;
  font-size: 12px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
`;

interface ModuleSummaryTestProps {
  moduleName: string;
}

const ModuleSummaryTest: React.FC<ModuleSummaryTestProps> = ({ moduleName }) => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log(`测试获取模块摘要: ${moduleName}`);
      const url = `/api/module_summary/${encodeURIComponent(moduleName)}`;
      console.log(`请求URL: ${url}`);
      
      const response = await fetch(url);
      console.log(`响应状态: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log('获取到模块摘要数据:', data);
        setSummary(data);
      } else {
        const errorText = await response.text();
        console.error(`获取模块摘要失败: ${errorText}`);
        setError(`获取失败: ${response.status} - ${errorText}`);
      }
    } catch (err) {
      console.error('获取模块摘要出错:', err);
      setError(`获取出错: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (moduleName) {
      fetchSummary();
    }
  }, [moduleName]);

  return (
    <TestContainer>
      <h3>模块摘要测试</h3>
      <p>模块名称: {moduleName}</p>
      
      <Button onClick={fetchSummary} disabled={loading}>
        {loading ? '加载中...' : '刷新摘要'}
      </Button>
      
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      
      {summary ? (
        <Pre>{JSON.stringify(summary, null, 2)}</Pre>
      ) : (
        <p>{loading ? '加载中...' : '无数据'}</p>
      )}
    </TestContainer>
  );
};

export default ModuleSummaryTest;
