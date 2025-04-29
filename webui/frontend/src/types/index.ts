export interface GlobalState {
  requirements: Requirement[];
  modules: Module[];
  techStack: TechStack[];
  validationIssues: ValidationIssue[];
  circularDependencies: CircularDependency[];
  mode: string;
}

export interface Requirement {
  id: string;
  name: string;
  description: string;
  priority: string;
  status: string;
  relatedModules?: string[];
}

export interface Module {
  id: string;
  name: string;
  description: string;
  responsibilities: string[];
  dependencies: string[];
  layer: string;
  domain: string;
  relatedRequirements?: string[];
}

export interface TechStack {
  id: string;
  name: string;
  category: string;
  description: string;
}

export interface ValidationIssue {
  id: string;
  type: string;
  description: string;
  relatedItems: string[];
  severity: string;
}

export interface CircularDependency {
  id: string;
  modules: string[];
  description: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
