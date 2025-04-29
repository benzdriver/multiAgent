import api from './client';
import { GlobalState, Requirement, Module, ValidationIssue, CircularDependency, ApiResponse } from '../types';

export const fetchGlobalState = (): Promise<ApiResponse<GlobalState>> => {
  return api.get<GlobalState>('/get_global_state');
};

export const refreshGlobalState = (): Promise<ApiResponse<GlobalState>> => {
  return api.get<GlobalState>('/refresh_global_state');
};

export const startClarifier = (): Promise<ApiResponse<{ message: string }>> => {
  return api.post<{ message: string }>('/start_clarifier');
};

export const checkDependencies = (): Promise<ApiResponse<{
  validationIssues: ValidationIssue[],
  circularDependencies: CircularDependency[]
}>> => {
  return api.get<{
    validationIssues: ValidationIssue[],
    circularDependencies: CircularDependency[]
  }>('/check_dependencies');
};

export const getDeepReasoningResults = (moduleId: string): Promise<ApiResponse<{
  result: string
}>> => {
  return api.get<{ result: string }>(`/get_deep_reasoning_results/${moduleId}`);
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
  refreshGlobalState,
  startClarifier,
  checkDependencies,
  getDeepReasoningResults,
  getRelatedModules,
  getRelatedRequirements,
};

export default services;
