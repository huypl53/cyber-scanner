import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ThreatPrediction {
  id: number;
  traffic_data_id: number;
  prediction_score: number;
  is_attack: boolean;
  threshold: number;
  model_version: string;
  created_at: string;
}

export interface AttackPrediction {
  id: number;
  traffic_data_id: number;
  attack_type_encoded: number;
  attack_type_name: string;
  confidence: number;
  model_version: string;
  created_at: string;
}

export interface SelfHealingAction {
  id: number;
  attack_prediction_id: number;
  action_type: string;
  action_description: string;
  action_params: Record<string, any>;
  status: string;
  created_at: string;
  execution_time?: string;
  error_message?: string;
}

export interface TrafficData {
  id: number;
  features: Record<string, any>;
  source: string;
  batch_id?: string;
  created_at: string;
}

export interface CompletePrediction {
  traffic_data: TrafficData;
  threat_prediction: ThreatPrediction;
  attack_prediction?: AttackPrediction;
  self_healing_action?: SelfHealingAction;
}

export interface PredictionStats {
  total_predictions: number;
  total_attacks: number;
  total_normal: number;
  attack_rate: number;
  attack_type_distribution: Record<string, number>;
  recent_predictions: CompletePrediction[];
}

// IP Whitelist interfaces
export interface IPWhitelist {
  id: number;
  ip_address: string;
  description?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  created_by?: string;
}

export interface IPWhitelistCreate {
  ip_address: string;
  description?: string;
  is_active?: boolean;
}

export interface IPWhitelistUpdate {
  description?: string;
  is_active?: boolean;
}

// Data Source Configuration interfaces
export interface DataSourceConfig {
  id: number;
  source_name: string;
  is_enabled: boolean;
  description?: string;
  config_params?: Record<string, any>;
  updated_at: string;
}

export interface DataSourceConfigUpdate {
  is_enabled: boolean;
  config_params?: Record<string, any>;
}

// Upload CSV file
export const uploadCSV = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/v1/upload/csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Get prediction statistics
export const getPredictionStats = async (): Promise<PredictionStats> => {
  const response = await api.get('/api/v1/predictions/stats');
  return response.data;
};

// Get recent predictions
export const getRecentPredictions = async (limit: number = 100): Promise<CompletePrediction[]> => {
  const response = await api.get(`/api/v1/predictions/recent?limit=${limit}`);
  return response.data;
};

// Get attack distribution
export const getAttackDistribution = async () => {
  const response = await api.get('/api/v1/predictions/attack-distribution');
  return response.data;
};

// Get action distribution
export const getActionDistribution = async () => {
  const response = await api.get('/api/v1/predictions/action-distribution');
  return response.data;
};

// Get list of uploaded batches
export const getUploadedBatches = async () => {
  const response = await api.get('/api/v1/upload/batches');
  return response.data;
};

// Get batch predictions
export const getBatchPredictions = async (batchId: string) => {
  const response = await api.get(`/api/v1/upload/batch/${batchId}`);
  return response.data;
};

// Start test data stream
export const startTestStream = async (config: {
  count: number;
  interval: number;
  model_type: string;
}) => {
  const response = await api.post('/api/v1/test/start-stream', config);
  return response.data;
};

// ========== Data Source Configuration API ==========

// Get all data sources
export const getDataSources = async (): Promise<DataSourceConfig[]> => {
  const response = await api.get('/api/v1/config/sources');
  return response.data;
};

// Get specific data source
export const getDataSource = async (sourceName: string): Promise<DataSourceConfig> => {
  const response = await api.get(`/api/v1/config/sources/${sourceName}`);
  return response.data;
};

// Update data source (enable/disable)
export const updateDataSource = async (
  sourceName: string,
  data: DataSourceConfigUpdate
): Promise<DataSourceConfig> => {
  const response = await api.patch(`/api/v1/config/sources/${sourceName}`, data);
  return response.data;
};

// ========== IP Whitelist API ==========

// Get all whitelisted IPs
export const getWhitelist = async (activeOnly: boolean = false): Promise<IPWhitelist[]> => {
  const response = await api.get('/api/v1/config/whitelist', {
    params: { active_only: activeOnly }
  });
  return response.data;
};

// Get specific whitelist entry
export const getWhitelistEntry = async (ipId: number): Promise<IPWhitelist> => {
  const response = await api.get(`/api/v1/config/whitelist/${ipId}`);
  return response.data;
};

// Add IP to whitelist
export const addIPToWhitelist = async (data: IPWhitelistCreate): Promise<IPWhitelist> => {
  const response = await api.post('/api/v1/config/whitelist', data);
  return response.data;
};

// Update whitelist entry
export const updateWhitelistEntry = async (
  ipId: number,
  data: IPWhitelistUpdate
): Promise<IPWhitelist> => {
  const response = await api.patch(`/api/v1/config/whitelist/${ipId}`, data);
  return response.data;
};

// Delete IP from whitelist
export const deleteIP = async (ipId: number): Promise<void> => {
  await api.delete(`/api/v1/config/whitelist/${ipId}`);
};

// ========== ML Model Management API ==========

export interface MLModel {
  id: number;
  model_type: string;
  version: string;
  file_path: string;
  file_format: string;
  original_filename: string;
  is_active: boolean;
  model_metadata?: Record<string, any>;
  validation_results?: Record<string, any>;
  file_size_bytes?: number;
  created_at: string;
  uploaded_by?: string;
  description?: string;
}

export interface MLModelListResponse {
  models: MLModel[];
  total_count: number;
}

export interface MLModelStorageStats {
  total_models: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_type: Record<string, any>;
  active_models: Array<{
    model_type: string;
    version: string;
    id: number;
  }>;
}

// Upload a new model
export const uploadModel = async (
  file: File,
  modelType: string,
  description?: string
): Promise<MLModel> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model_type', modelType);
  if (description) {
    formData.append('description', description);
  }

  const response = await api.post('/api/v1/models/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Get all models
export const getModels = async (
  modelType?: string,
  includeInactive: boolean = true
): Promise<MLModelListResponse> => {
  const params: Record<string, any> = {
    include_inactive: includeInactive,
  };
  if (modelType) {
    params.model_type = modelType;
  }

  const response = await api.get('/api/v1/models/', { params });
  return response.data;
};

// Get specific model
export const getModel = async (modelId: number): Promise<MLModel> => {
  const response = await api.get(`/api/v1/models/${modelId}`);
  return response.data;
};

// Activate a model
export const activateModel = async (modelId: number): Promise<MLModel> => {
  const response = await api.post(`/api/v1/models/${modelId}/activate`);
  return response.data;
};

// Deactivate a model
export const deactivateModel = async (modelId: number): Promise<MLModel> => {
  const response = await api.post(`/api/v1/models/${modelId}/deactivate`);
  return response.data;
};

// Delete a model
export const deleteModel = async (modelId: number, deleteFile: boolean = true): Promise<void> => {
  await api.delete(`/api/v1/models/${modelId}`, {
    params: { delete_file: deleteFile },
  });
};

// Get storage statistics
export const getModelStorageStats = async (): Promise<MLModelStorageStats> => {
  const response = await api.get('/api/v1/models/stats/storage');
  return response.data;
};

// Get supported formats info
export const getModelSupportedFormats = async () => {
  const response = await api.get('/api/v1/models/info/supported-formats');
  return response.data;
};

export default api;
