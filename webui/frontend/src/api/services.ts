import api from './client';
import { GlobalState, Requirement, Module, ApiResponse } from '../types';

export const fetchGlobalState = (): Promise<ApiResponse<GlobalState>> => {
  return api.get<GlobalState>('/state/get_global_state');
};

export const getConversationHistory = (): Promise<ApiResponse<Array<{role: string, content: string}>>> => {
  return api.get<Array<{role: string, content: string}>>('/history');
};

export const getCurrentMode = (): Promise<ApiResponse<{mode: string}>> => {
  return api.get<{mode: string}>('/mode');
};

export const startClarifier = (): Promise<ApiResponse<{ status: string, message: string }>> => {
  return api.post<{ status: string, message: string }>('/start_clarifier');
};

export const analyzeRequirements = (): Promise<ApiResponse<{
  status: string,
  message: string,
  modules_count: number
}>> => {
  return api.post<{
    status: string,
    message: string,
    modules_count: number
  }>('/analyze');
};

export const generateGranularModules = (): Promise<ApiResponse<{
  status: string,
  message: string,
  new_modules_count: number
}>> => {
  return api.post<{
    status: string,
    message: string,
    new_modules_count: number
  }>('/granular_modules');
};

export const checkConflicts = (): Promise<ApiResponse<{
  status: string,
  message: string,
  conflicts: Array<any>
}>> => {
  return api.post<{
    status: string,
    message: string,
    conflicts: Array<any>
  }>('/conflict_check');
};

export const setMode = (mode: string): Promise<ApiResponse<{
  status: string,
  mode: string
}>> => {
  const formData = new FormData();
  formData.append('mode', mode);
  
  return api.post<{
    status: string,
    mode: string
  }>('/set_mode', formData);
};

export const uploadFile = (file: File): Promise<ApiResponse<{
  status: string,
  filename: string
}>> => {
  return api.upload<{
    status: string,
    filename: string
  }>('/upload_file', file);
};

export const analyzeDocuments = (): Promise<ApiResponse<{
  status: string,
  message: string,
  global_state: GlobalState
}>> => {
  return api.post<{
    status: string,
    message: string,
    global_state: GlobalState
  }>('/analyze_documents');
};

export const updateRequirement = (reqId: string, data: any): Promise<ApiResponse<{
  status: string,
  requirement: Requirement,
  affected_modules: string[]
}>> => {
  return api.post<{
    status: string,
    requirement: Requirement,
    affected_modules: string[]
  }>(`/update_requirement/${reqId}`, data);
};

export const deepClarification = (): Promise<ApiResponse<{
  status: string,
  message: string
}>> => {
  return api.post<{
    status: string,
    message: string
  }>('/deep_clarification');
};

export const deepReasoning = (): Promise<ApiResponse<{
  status: string,
  message: string,
  has_extracted_json: boolean
}>> => {
  return api.post<{
    status: string,
    message: string,
    has_extracted_json: boolean
  }>('/deep_reasoning');
};

export const checkDependencies = (): Promise<ApiResponse<{
  status: string,
  circular_dependencies: Array<any>,
  validation_issues: Array<any>
}>> => {
  return api.get<{
    status: string,
    circular_dependencies: Array<any>,
    validation_issues: Array<any>
  }>('/check_dependencies');
};

export const getRelatedModules = (requirementId: string): Promise<ApiResponse<{
  modules: Module[]
}>> => {
  return api.get<{ modules: Module[] }>(`/get_related_modules/${requirementId}`);
};

export const getRelatedRequirements = (moduleId: string): Promise<ApiResponse<{
  requirements: Requirement[]
}>> => {
  return api.get<{ requirements: Requirement[] }>(`/get_related_requirements/${moduleId}`);
};

export const services = {
  fetchGlobalState,
  getConversationHistory,
  getCurrentMode,
  
  startClarifier,
  analyzeRequirements,
  generateGranularModules,
  checkConflicts,
  
  setMode,
  uploadFile,
  analyzeDocuments,
  updateRequirement,
  
  deepClarification,
  deepReasoning,
  checkDependencies,
  
  getRelatedModules,
  getRelatedRequirements
};

export default services;
