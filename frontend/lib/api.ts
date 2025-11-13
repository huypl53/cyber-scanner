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

export default api;
