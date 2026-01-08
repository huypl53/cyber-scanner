'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
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
  const t = useTranslations('models');
  const locale = useLocale();
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
      setError(t('errors.loadFailed', { error: err.response?.data?.detail || err.message }));
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
        setError(t('upload.errors.invalidFormat'));
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
      setError(t('upload.errors.selectFile'));
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
          setError(t('upload.errors.invalidJson'));
          setUploading(false);
          return;
        }
      }

      const uploadedModel = await uploadModel(selectedFile, modelType, description, profileConfig);
      setSuccess(t('success.uploaded', { version: uploadedModel.version }));
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
      setError(t('errors.uploadFailed', { error: err.response?.data?.detail || err.message }));
    } finally {
      setUploading(false);
    }
  };

  const handleActivate = async (modelId: number) => {
    try {
      setError('');
      setSuccess('');
      await activateModel(modelId);
      setSuccess(t('success.activated'));
      await loadModels();
      await loadStats();
    } catch (err: any) {
      setError(t('errors.activationFailed', { error: err.response?.data?.detail || err.message }));
    }
  };

  const handleDeactivate = async (modelId: number) => {
    try {
      setError('');
      setSuccess('');
      await deactivateModel(modelId);
      setSuccess(t('success.deactivated'));
      await loadModels();
      await loadStats();
    } catch (err: any) {
      setError(t('errors.deactivationFailed', { error: err.response?.data?.detail || err.message }));
    }
  };

  const handleDelete = async (modelId: number) => {
    if (!confirm(t('list.confirmDelete'))) {
      return;
    }

    try {
      setError('');
      setSuccess('');
      await deleteModel(modelId, true);
      setSuccess(t('success.deleted'));
      await loadModels();
      await loadStats();
    } catch (err: any) {
      setError(t('errors.deletionFailed', { error: err.response?.data?.detail || err.message }));
    }
  };

  const formatBytes = (bytes: number | undefined) => {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString(locale);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gradient-cyan mb-2">{t('title')}</h1>
        <p className="text-muted-foreground">{t('subtitle')}</p>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-6 bg-destructive/10 border border-destructive/30 text-destructive px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-6 bg-status-safe/10 border border-status-safe/30 text-status-safe px-4 py-3 rounded-lg">
          {success}
        </div>
      )}

      {/* Storage Statistics */}
      {stats && (
        <div className="bg-card shadow-glow border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">{t('stats.title')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-primary/10 p-4 rounded-lg border border-primary/20">
              <div className="text-sm text-muted-foreground">{t('stats.totalModels')}</div>
              <div className="text-2xl font-bold text-primary">{stats.total_models}</div>
            </div>
            <div className="bg-status-safe/10 p-4 rounded-lg border border-status-safe/20">
              <div className="text-sm text-muted-foreground">{t('stats.totalSize')}</div>
              <div className="text-2xl font-bold text-status-safe">{stats.total_size_mb.toFixed(2)} MB</div>
            </div>
            <div className="bg-amber-500/10 p-4 rounded-lg border border-amber-500/20">
              <div className="text-sm text-muted-foreground">{t('stats.threatDetector')}</div>
              <div className="text-2xl font-bold text-amber-500">
                {stats.by_type.threat_detector?.count || 0}
              </div>
            </div>
            <div className="bg-pink-500/10 p-4 rounded-lg border border-pink-500/20">
              <div className="text-sm text-muted-foreground">{t('stats.attackClassifier')}</div>
              <div className="text-2xl font-bold text-pink-500">
                {stats.by_type.attack_classifier?.count || 0}
              </div>
            </div>
          </div>

          {stats.active_models.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="text-sm font-medium text-card-foreground mb-2">{t('stats.activeModels')}</div>
              <div className="space-y-1">
                {stats.active_models.map((active) => (
                  <div key={active.id} className="text-sm text-muted-foreground">
                    <span className="font-medium text-card-foreground">{active.model_type}</span>: v{active.version}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Active Model Profiles */}
      {Object.keys(activeProfiles).length > 0 && (
        <div className="bg-card shadow-glow border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">{t('profiles.title')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(activeProfiles).map(([modelType, profile]) => (
              <div key={modelType} className="border border-border rounded-lg p-4 bg-muted/20">
                <h3 className="font-medium text-card-foreground mb-3">
                  {modelType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                {profile.expected_features && profile.expected_features.length > 0 && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-card-foreground mb-1">
                      {t('profiles.features')} ({profile.expected_features.length})
                    </div>
                    <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2 max-h-32 overflow-y-auto border border-border">
                      {profile.expected_features.slice(0, 5).join(', ')}
                      {profile.expected_features.length > 5 && ` ... and ${profile.expected_features.length - 5} more`}
                    </div>
                  </div>
                )}
                {profile.class_labels && profile.class_labels.length > 0 && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-card-foreground mb-1">
                      {t('profiles.classes')} ({profile.class_labels.length})
                    </div>
                    <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2 border border-border">
                      {profile.class_labels.join(', ')}
                    </div>
                  </div>
                )}
                {profile.preprocessing_notes && (
                  <div>
                    <div className="text-sm font-medium text-card-foreground mb-1">{t('profiles.notes')}</div>
                    <div className="text-xs text-muted-foreground">{profile.preprocessing_notes}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Form */}
      <div className="bg-card shadow-glow border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">{t('upload.title')}</h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-2">
              {t('upload.modelType')}
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full border border-border rounded-md px-3 py-2 bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="threat_detector">{t('upload.threatDetectorOption')}</option>
              <option value="attack_classifier">{t('upload.attackClassifierOption')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-card-foreground mb-2">
              {t('upload.fileLabel')}
            </label>
            <input
              id="file-input"
              type="file"
              accept=".pkl,.joblib,.h5"
              onChange={handleFileSelect}
              className="w-full border border-border rounded-md px-3 py-2 bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {selectedFile && (
              <p className="mt-2 text-sm text-muted-foreground">
                {t('upload.selected')}: {selectedFile.name} ({formatBytes(selectedFile.size)})
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-card-foreground mb-2">
              {t('upload.descriptionLabel')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('upload.descriptionPlaceholder')}
              rows={3}
              className="w-full border border-border rounded-md px-3 py-2 bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="border-t border-border pt-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-card-foreground">
                {t('upload.customProfile')}
              </label>
              <button
                type="button"
                onClick={() => setShowProfileInput(!showProfileInput)}
                className="text-sm text-primary hover:text-primary/80"
              >
                {showProfileInput ? t('upload.hide') : t('upload.show')}
              </button>
            </div>
            {showProfileInput && (
              <div>
                <p className="text-xs text-muted-foreground mb-2">
                  {t('upload.profileHint')}
                </p>
                <textarea
                  value={profileConfigJson}
                  onChange={(e) => setProfileConfigJson(e.target.value)}
                  placeholder={`{\n  "expected_features": ["feature1", "feature2", ...],\n  "class_labels": ["class1", "class2", ...],\n  "preprocessing_notes": "Optional notes"\n}`}
                  rows={6}
                  className="w-full border border-border rounded-md px-3 py-2 bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary font-mono text-xs"
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
              !selectedFile || uploading
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-primary text-primary-foreground hover:bg-primary/90'
            }`}
          >
            {uploading ? t('upload.uploading') : t('upload.uploadButton')}
          </button>
        </form>
      </div>

      {/* Models List */}
      <div className="bg-card shadow-glow border border-border rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">{t('list.title')}</h2>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="border border-border rounded-md px-3 py-2 text-sm bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">{t('list.filterAll')}</option>
            <option value="threat_detector">{t('list.filterThreatDetector')}</option>
            <option value="attack_classifier">{t('list.filterAttackClassifier')}</option>
          </select>
        </div>

        {loading ? (
          <div className="text-center py-8 text-muted-foreground">{t('list.loading')}</div>
        ) : models.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">{t('list.noModels')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.type')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.version')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.filename')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.status')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.size')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.uploaded')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('list.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-card divide-y divide-border">
                {models.map((model) => (
                  <tr key={model.id} className={model.is_active ? 'bg-status-safe/10' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-card-foreground">
                      {model.model_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {model.version}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {model.original_filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {model.is_active ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-status-safe/20 text-status-safe">
                          {t('list.table.active')}
                        </span>
                      ) : (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-muted text-muted-foreground">
                          {t('list.table.inactive')}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {formatBytes(model.file_size_bytes)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {formatDate(model.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {!model.is_active ? (
                        <button
                          onClick={() => handleActivate(model.id)}
                          className="text-status-safe hover:text-status-safe/80"
                        >
                          {t('list.actions.activate')}
                        </button>
                      ) : (
                        <button
                          onClick={() => handleDeactivate(model.id)}
                          className="text-amber-500 hover:text-amber-600"
                        >
                          {t('list.actions.deactivate')}
                        </button>
                      )}
                      {!model.is_active && (
                        <button
                          onClick={() => handleDelete(model.id)}
                          className="text-destructive hover:text-destructive/80"
                        >
                          {t('list.actions.delete')}
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
