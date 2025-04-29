import { useState, useCallback } from 'react';
import { ApiResponse } from '../types';

export function useApi<T, P = any>(
  apiFunction: (params?: P) => Promise<T>
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
        
        if (response && typeof response === 'object' && ('status' in response || 'error' in response)) {
          const apiResponse = response as unknown as ApiResponse;
          
          if (apiResponse.error) {
            setError(apiResponse.error);
            setIsLoading(false);
            return null;
          }
        }
        
        setData(response);
        setIsLoading(false);
        return response;
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
