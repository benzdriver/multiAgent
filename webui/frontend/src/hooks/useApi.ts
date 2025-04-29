import { useState, useCallback } from 'react';
import { ApiResponse } from '../types';

export function useApi<T, P = any>(
  apiFunction: (params?: P) => Promise<ApiResponse<T>>
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (params?: P): Promise<T | null> => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiFunction(params);
        
        if (response.success && response.data) {
          setData(response.data);
          setIsLoading(false);
          return response.data;
        } else {
          setError(response.error || '请求失败');
          setIsLoading(false);
          return null;
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '未知错误';
        setError(errorMessage);
        setIsLoading(false);
        return null;
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setData(null);
    setIsLoading(false);
    setError(null);
  }, []);

  return {
    data,
    isLoading,
    error,
    execute,
    reset
  };
}

export default useApi;
