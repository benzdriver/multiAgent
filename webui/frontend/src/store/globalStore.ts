import { create } from 'zustand';
import { GlobalState, Requirement, Module } from '../types';
import services from '../api/services';

declare global {
  interface Window {
    __GLOBAL_STATE__: GlobalState;
  }
}

interface GlobalStore {
  state: GlobalState;
  isLoading: boolean;
  error: string | null;
  
  fetchGlobalState: () => Promise<void>;
  getConversationHistory: () => Promise<Array<{role: string, content: string}>>;
  getCurrentMode: () => Promise<string>;
  
  startClarifier: () => Promise<void>;
  analyzeRequirements: () => Promise<void>;
  generateGranularModules: () => Promise<void>;
  checkConflicts: () => Promise<void>;
  
  setMode: (mode: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  analyzeDocuments: () => Promise<void>;
  updateRequirement: (reqId: string, data: any) => Promise<void>;
  
  deepClarification: () => Promise<void>;
  deepReasoning: () => Promise<void>;
  checkDependencies: () => Promise<void>;
  
  getRelatedModules: (requirementId: string) => Promise<Module[]>;
  getRelatedRequirements: (moduleId: string) => Promise<Requirement[]>;
}

const initialState: GlobalState = {
  requirements: [],
  modules: [],
  techStack: [],
  validationIssues: [],
  circularDependencies: [],
  mode: 'default',
};

export const useGlobalStore = create<GlobalStore>((set, get) => {
  const store = {
  state: initialState,
  isLoading: false,
  error: null,
  
  fetchGlobalState: async () => {
    set({ isLoading: true, error: null });
    try {
      console.log('开始获取全局状态...');
      const response = await services.fetchGlobalState();
      console.log('获取全局状态响应:', response);
      
      if (response) {
        if (response.data) {
          console.log('响应数据模块:', response.data.modules);
          set({ state: response.data, isLoading: false });
          console.log('设置后的全局状态:', get().state);
          console.log('设置后的模块列表:', get().state.modules);
        } else if ('requirements' in response && Array.isArray((response as any).requirements)) {
          console.log('响应直接包含requirements:', (response as any).requirements);
          set({ state: response as unknown as GlobalState, isLoading: false });
          console.log('设置后的全局状态:', get().state);
        } else {
          throw new Error('获取全局状态失败：无数据');
        }
      } else {
        throw new Error('获取全局状态失败：无响应');
      }
    } catch (error) {
      console.error('获取全局状态时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '获取全局状态失败', 
        isLoading: false 
      });
    }
  },
  
  getConversationHistory: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getConversationHistory();
      set({ isLoading: false });
      return response.data || [];
    } catch (error) {
      console.error('获取对话历史时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '获取对话历史失败', 
        isLoading: false 
      });
      return [];
    }
  },
  
  getCurrentMode: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getCurrentMode();
      set({ isLoading: false });
      return response.data?.mode || 'default';
    } catch (error) {
      console.error('获取当前模式时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '获取当前模式失败', 
        isLoading: false 
      });
      return 'default';
    }
  },
  
  startClarifier: async () => {
    set({ isLoading: true, error: null });
    try {
      console.log('开始启动澄清器...');
      const response = await services.startClarifier();
      console.log('澄清器启动响应:', response);
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('启动澄清器时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '启动澄清器失败', 
        isLoading: false 
      });
    }
  },
  
  analyzeRequirements: async () => {
    set({ isLoading: true, error: null });
    try {
      await services.analyzeRequirements();
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('分析需求时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '分析需求失败', 
        isLoading: false 
      });
    }
  },
  
  generateGranularModules: async () => {
    set({ isLoading: true, error: null });
    try {
      await services.generateGranularModules();
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('生成细粒度模块时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '生成细粒度模块失败', 
        isLoading: false 
      });
    }
  },
  
  checkConflicts: async () => {
    set({ isLoading: true, error: null });
    try {
      await services.checkConflicts();
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('检查冲突时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '检查冲突失败', 
        isLoading: false 
      });
    }
  },
  
  setMode: async (mode: string) => {
    set({ isLoading: true, error: null });
    try {
      await services.setMode(mode);
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('设置模式时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '设置模式失败', 
        isLoading: false 
      });
    }
  },
  
  uploadFile: async (file: File) => {
    set({ isLoading: true, error: null });
    try {
      await services.uploadFile(file);
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('上传文件时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '上传文件失败', 
        isLoading: false 
      });
    }
  },
  
  analyzeDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      await services.analyzeDocuments();
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('分析文档时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '分析文档失败', 
        isLoading: false 
      });
    }
  },
  
  updateRequirement: async (reqId: string, data: any) => {
    set({ isLoading: true, error: null });
    try {
      await services.updateRequirement(reqId, data);
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('更新需求时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '更新需求失败', 
        isLoading: false 
      });
    }
  },
  
  deepClarification: async () => {
    set({ isLoading: true, error: null });
    try {
      await services.deepClarification();
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('深度澄清时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '深度澄清失败', 
        isLoading: false 
      });
    }
  },
  
  deepReasoning: async () => {
    set({ isLoading: true, error: null });
    try {
      await services.deepReasoning();
      await get().fetchGlobalState();
      set({ isLoading: false });
    } catch (error) {
      console.error('深度推理时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '深度推理失败', 
        isLoading: false 
      });
    }
  },
  
  checkDependencies: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.checkDependencies();
      set(state => ({
        state: {
          ...state.state,
          validationIssues: response.data?.validation_issues || [],
          circularDependencies: response.data?.circular_dependencies || []
        },
        isLoading: false
      }));
    } catch (error) {
      console.error('检查依赖时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '检查依赖失败', 
        isLoading: false 
      });
    }
  },
  
  getRelatedModules: async (requirementId: string): Promise<Module[]> => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getRelatedModules(requirementId);
      set({ isLoading: false });
      return response.data?.modules || [];
    } catch (error) {
      console.error('获取相关模块时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '获取相关模块失败', 
        isLoading: false 
      });
      return [];
    }
  },
  
  getRelatedRequirements: async (moduleId: string): Promise<Requirement[]> => {
    set({ isLoading: true, error: null });
    try {
      const response = await services.getRelatedRequirements(moduleId);
      set({ isLoading: false });
      return response.data?.requirements || [];
    } catch (error) {
      console.error('获取相关需求时出错:', error);
      set({ 
        error: error instanceof Error ? error.message : '获取相关需求失败', 
        isLoading: false 
      });
      return [];
    }
  }
  };
  
  if (typeof window !== 'undefined') {
    window.__GLOBAL_STATE__ = initialState;
    
    console.log('🔄 初始化全局状态:', initialState);
    
    const updateWindow = () => {
      window.__GLOBAL_STATE__ = get().state;
      console.log('🔄 更新全局状态:', get().state);
    };
    
    setTimeout(updateWindow, 1000);
    
    setInterval(updateWindow, 1000);
  }
  
  return store;
});

export default useGlobalStore;
