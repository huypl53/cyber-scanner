'use client';

import { useState, useEffect } from 'react';
import {
  getModels,
  uploadModel,
  activateModel,
  deactivateModel,
  deleteModel,
  getModelStorageStats,
  getActiveModelProfile,
  MLModel,
  MLModelListResponse,
  MLModelStorageStats,
  ModelProfile,
} from '@/lib/api';

export default function ModelsPage() {
  // State
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<MLModelStorageStats | null>(null);

  // Upload form state
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modelType, setModelType] = useState<string>('threat_detector');
  const [description, setDescription] = useState<string>('');
  const [profileConfigJson, setProfileConfigJson] = useState<string>('');
  const [showProfileInput, setShowProfileInput] = useState(false);

  // Active model profiles
  const [activeProfiles, setActiveProfiles] = useState<Record<string, ModelProfile>>({});

  // UI state
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    loadModels();
    loadStats();
    loadActiveProfiles();
  }, [filterType]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const modelTypeFilter = filterType === 'all' ? undefined : filterType;
      const response: MLModelListResponse = await getModels(modelTypeFilter, true);
      setModels(response.models);
    } catch (err: any) {
      setError('Failed to load models: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await getModelStorageStats();
      setStats(statsData);
    } catch (err: any) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadActiveProfiles = async () => {
    try {
      const threatProfile = await getActiveModelProfile('threat_detector');
      const attackProfile = await getActiveModelProfile('attack_classifier');
      setActiveProfiles({
        'threat_detector': threatProfile.profile,
        'attack_classifier': attackProfile.profile,
      });
    } catch (err: any) {
      console.error('Failed to load active profiles:', err);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.split('.').pop()?.toLowerCase();

      if (!['pkl', 'joblib', 'h5'].includes(ext || '')) {
        setError('Invalid file format. Supported: .pkl, .joblib, .h5');
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
      setError('');
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      // Parse profile config if provided
      let profileConfig: ModelProfile | undefined = undefined;
      if (profileConfigJson.trim()) {
        try {
          profileConfig = JSON.parse(profileConfigJson);
        } catch (parseErr) {
          setError('Invalid JSON in profile configuration');
          setUploading(false);
          return;
        }
      }

      const uploadedModel = await uploadModel(selectedFile, modelType, description, profileConfig);
      setSuccess(`Model uploaded successfully! Version: ${uploadedModel.version}`);
      setSelectedFile(null);
      setDescription('');
      setProfileConfigJson('');
      setShowProfileInput(false);

      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      // Reload models, stats, and active profiles
      await loadModels();
      await loadStats();
      await loadActiveProfiles();
    } catch (err: any) {
      setError('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (modelId: number) => {
    try {
      setError('');
      setSuccess('');
      await activateModel(modelId);
      setSuccess('Model activated successfully');
      await loadModels();
      await loadStats();
    } catch (err: any) {
      setError('Activation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeactivate = async (modelId: number) => {
    try {
      setError('');
      setSuccess('');
      await deactivateModel(modelId);
      setSuccess('Model deactivated successfully');
      await loadModels();
      await loadStats();
    } catch (err: any) {
      setError('Deactivation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (modelId: number) => {
    if (!confirm('Are you sure you want to delete this model? This action cannot be undone.')) {
      return;
    }

    try {
      setError('');
      setSuccess('');
      await deleteModel(modelId, true);
      setSuccess('Model deleted successfully');
      await loadModels();
      await loadStats();
    } catch (err: any) {
      setError('Deletion failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const formatBytes = (bytes: number | undefined) => {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="px-4 py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Model Management</h1>
        <p className="text-gray-600">Upload, manage, and activate ML models for threat detection and attack classification</p>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {success}
        </div>
      )}

      {/* Storage Statistics */}
      {stats && (
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Storage Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Models</div>
              <div className="text-2xl font-bold text-blue-600">{stats.total_models}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Size</div>
              <div className="text-2xl font-bold text-green-600">{stats.total_size_mb.toFixed(2)} MB</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Threat Detector</div>
              <div className="text-2xl font-bold text-purple-600">
                {stats.by_type.threat_detector?.count || 0}
              </div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Attack Classifier</div>
              <div className="text-2xl font-bold text-orange-600">
                {stats.by_type.attack_classifier?.count || 0}
              </div>
            </div>
          </div>

          {stats.active_models.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <div className="text-sm font-medium text-gray-700 mb-2">Active Models:</div>
              <div className="space-y-1">
                {stats.active_models.map((active) => (
                  <div key={active.id} className="text-sm text-gray-600">
                    <span className="font-medium">{active.model_type}</span>: v{active.version}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Active Model Profiles */}
      {Object.keys(activeProfiles).length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Active Model Profiles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(activeProfiles).map(([modelType, profile]) => (
              <div key={modelType} className="border rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">
                  {modelType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                {profile.expected_features && profile.expected_features.length > 0 && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      Features ({profile.expected_features.length})
                    </div>
                    <div className="text-xs text-gray-600 bg-gray-50 rounded p-2 max-h-32 overflow-y-auto">
                      {profile.expected_features.slice(0, 5).join(', ')}
                      {profile.expected_features.length > 5 && ` ... and ${profile.expected_features.length - 5} more`}
                    </div>
                  </div>
                )}
                {profile.class_labels && profile.class_labels.length > 0 && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      Classes ({profile.class_labels.length})
                    </div>
                    <div className="text-xs text-gray-600 bg-gray-50 rounded p-2">
                      {profile.class_labels.join(', ')}
                    </div>
                  </div>
                )}
                {profile.preprocessing_notes && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-1">Notes</div>
                    <div className="text-xs text-gray-600">{profile.preprocessing_notes}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Form */}
      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Upload New Model</h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Type
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="threat_detector">Threat Detector (10 features)</option>
              <option value="attack_classifier">Attack Classifier (42 features)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model File (.pkl, .joblib, or .h5)
            </label>
            <input
              id="file-input"
              type="file"
              accept=".pkl,.joblib,.h5"
              onChange={handleFileSelect}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {selectedFile.name} ({formatBytes(selectedFile.size)})
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., LSTM model trained on NSL-KDD dataset"
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Custom Model Profile (Optional)
              </label>
              <button
                type="button"
                onClick={() => setShowProfileInput(!showProfileInput)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {showProfileInput ? 'Hide' : 'Show'}
              </button>
            </div>
            {showProfileInput && (
              <div>
                <p className="text-xs text-gray-500 mb-2">
                  Provide custom feature list and class labels as JSON. Leave empty to use defaults.
                </p>
                <textarea
                  value={profileConfigJson}
                  onChange={(e) => setProfileConfigJson(e.target.value)}
                  placeholder={`{\n  "expected_features": ["feature1", "feature2", ...],\n  "class_labels": ["class1", "class2", ...],\n  "preprocessing_notes": "Optional notes"\n}`}
                  rows={6}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs"
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className={`w-full py-2 px-4 rounded-md font-medium ${
              !selectedFile || uploading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {uploading ? 'Uploading...' : 'Upload Model'}
          </button>
        </form>
      </div>

      {/* Models List */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Uploaded Models</h2>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Models</option>
            <option value="threat_detector">Threat Detector</option>
            <option value="attack_classifier">Attack Classifier</option>
          </select>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading models...</div>
        ) : models.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No models uploaded yet</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Version
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Filename
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {models.map((model) => (
                  <tr key={model.id} className={model.is_active ? 'bg-green-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {model.model_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {model.version}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {model.original_filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {model.is_active ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatBytes(model.file_size_bytes)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(model.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {!model.is_active ? (
                        <button
                          onClick={() => handleActivate(model.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Activate
                        </button>
                      ) : (
                        <button
                          onClick={() => handleDeactivate(model.id)}
                          className="text-yellow-600 hover:text-yellow-900"
                        >
                          Deactivate
                        </button>
                      )}
                      {!model.is_active && (
                        <button
                          onClick={() => handleDelete(model.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
