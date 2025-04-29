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

export interface ApiResponse<T = any> {
  status?: string;
  message?: string;
  error?: string;
  data?: T;
}

export interface StateResponse extends GlobalState {
  status?: string;
}

export interface HistoryResponse {
  role: string;
  content: string;
}

export interface ModeResponse {
  mode: string;
}

export interface ClarifierResponse {
  status: string;
  message: string;
}

export interface AnalyzeResponse extends ClarifierResponse {
  modules_count: number;
}

export interface GranularModulesResponse extends ClarifierResponse {
  new_modules_count: number;
}

export interface ConflictCheckResponse extends ClarifierResponse {
  conflicts: Array<any>;
}

export interface SetModeResponse {
  status: string;
  mode: string;
}

export interface UploadFileResponse {
  status: string;
  filename: string;
}

export interface AnalyzeDocumentsResponse extends ClarifierResponse {
  global_state: GlobalState;
}

export interface UpdateRequirementResponse {
  status: string;
  requirement: Requirement;
  affected_modules: string[];
}

export interface DeepReasoningResponse extends ClarifierResponse {
  has_extracted_json: boolean;
}

export interface DependencyCheckResponse {
  status: string;
  validation_issues: ValidationIssue[];
  circular_dependencies: CircularDependency[];
}

export interface RelatedModulesResponse {
  modules: Module[];
}

export interface RelatedRequirementsResponse {
  requirements: Requirement[];
}
