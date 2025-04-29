import { create } from 'zustand';
import { GlobalState, Requirement, Module } from '../types';
import services from '../api/services';

const initialState: GlobalState = {
  requirements: [],
  modules: [],
  techStack: [],
  validationIssues: [],
  circularDependencies: [],
  mode: 'default',
};

export const useGlobalStore = create<{
  state: GlobalState;
  isLoading: boolean;
  error: string | null;
  
  fetchGlobalState: () => Promise<void>;
  refreshGlobalState: () => Promise<void>;
  startClarifier: () => Promise<void>;
  checkDependencies: () => Promise<void>;
  getDeepReasoningResults: (moduleId: string) => Promise<string>;
  getRelatedModules: (requirementId: string) => Promise<Module[]>;
  getRelatedRequirements: (moduleId: string) => Promise<Requirement[]>;
  setMode: (mode: string) => void;
}>((set, get) => ({
  state: initialState,
  isLoading: false,
  error: null,
  
  fetchGlobalState: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.fetchGlobalState();
      if (response.success && response.data) {
        set({ state: response.data, isLoading: false });
      } else {
        set({ error: response.error || '获取全局状态失败', isLoading: false });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
    }
  },
  
  refreshGlobalState: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.refreshGlobalState();
      if (response.success && response.data) {
        set({ state: response.data, isLoading: false });
      } else {
        set({ error: response.error || '刷新全局状态失败', isLoading: false });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
    }
  },
  
  startClarifier: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.startClarifier();
      if (response.success) {
        await get().refreshGlobalState();
      } else {
        set({ error: response.error || '启动澄清器失败', isLoading: false });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
    }
  },
  
  checkDependencies: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.checkDependencies();
      if (response.success && response.data) {
        set(state => ({
          state: {
            ...state.state,
            validationIssues: response.data?.validationIssues || [],
            circularDependencies: response.data?.circularDependencies || []
          },
          isLoading: false
        }));
      } else {
        set({ error: response.error || '检查依赖关系失败', isLoading: false });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
    }
  },
  
  getDeepReasoningResults: async (moduleId: string): Promise<string> => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getDeepReasoningResults(moduleId);
      set({ isLoading: false });
      if (response.success && response.data) {
        return response.data.result;
      } else {
        set({ error: response.error || '获取深度推理结果失败' });
        return '';
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
      return '';
    }
  },
  
  getRelatedModules: async (requirementId: string): Promise<Module[]> => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getRelatedModules(requirementId);
      set({ isLoading: false });
      if (response.success && response.data) {
        return response.data.modules;
      } else {
        set({ error: response.error || '获取相关模块失败' });
        return [];
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
      return [];
    }
  },
  
  getRelatedRequirements: async (moduleId: string): Promise<Requirement[]> => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getRelatedRequirements(moduleId);
      set({ isLoading: false });
      if (response.success && response.data) {
        return response.data.requirements;
      } else {
        set({ error: response.error || '获取相关需求失败' });
        return [];
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '未知错误', isLoading: false });
      return [];
    }
  },
  
  setMode: (mode: string) => {
    set(state => ({
      state: {
        ...state.state,
        mode
      }
    }));
  }
}));

export default useGlobalStore;
