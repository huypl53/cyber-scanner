'use client';

import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import {
  getDataSources,
  updateDataSource,
  getWhitelist,
  addIPToWhitelist,
  deleteIP,
  updateWhitelistEntry,
  DataSourceConfig,
  IPWhitelist,
} from '@/lib/api';

export default function SettingsPage() {
  const t = useTranslations('settings');
  const locale = useLocale();
  // Data source state
  const [sources, setSources] = useState<DataSourceConfig[]>([]);
  const [loadingSources, setLoadingSources] = useState(true);

  // IP whitelist state
  const [whitelist, setWhitelist] = useState<IPWhitelist[]>([]);
  const [loadingWhitelist, setLoadingWhitelist] = useState(true);

  // Form state
  const [newIP, setNewIP] = useState('');
  const [newIPDescription, setNewIPDescription] = useState('');
  const [formError, setFormError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoadingSources(true);
      setLoadingWhitelist(true);

      const [sourcesData, whitelistData] = await Promise.all([
        getDataSources(),
        getWhitelist(),
      ]);

      setSources(sourcesData);
      setWhitelist(whitelistData);
    } catch (error) {
      console.error('Error loading settings:', error);
      setFormError(t('ipWhitelist.errors.loadFailed'));
    } finally {
      setLoadingSources(false);
      setLoadingWhitelist(false);
    }
  };

  const handleToggleSource = async (sourceName: string, currentStatus: boolean) => {
    try {
      await updateDataSource(sourceName, { is_enabled: !currentStatus });
      const status = !currentStatus ? 'enabled' : 'disabled';
      setSuccessMessage(t('dataSources.toggleSuccess', { source: sourceName, status }));
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error) {
      console.error('Error toggling source:', error);
      setFormError(t('dataSources.toggleError', { source: sourceName }));
      setTimeout(() => setFormError(''), 3000);
    }
  };

  const validateIP = (ip: string): boolean => {
    // Basic IP validation (IPv4)
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipv4Regex.test(ip)) {
      return false;
    }

    // Check each octet is 0-255
    const octets = ip.split('.');
    return octets.every(octet => {
      const num = parseInt(octet, 10);
      return num >= 0 && num <= 255;
    });
  };

  const handleAddIP = async () => {
    setFormError('');
    setSuccessMessage('');

    if (!newIP.trim()) {
      setFormError(t('ipWhitelist.errors.ipRequired'));
      return;
    }

    if (!validateIP(newIP)) {
      setFormError(t('ipWhitelist.errors.invalidIP'));
      return;
    }

    try {
      await addIPToWhitelist({
        ip_address: newIP,
        description: newIPDescription || undefined,
        is_active: true,
      });

      setSuccessMessage(t('ipWhitelist.success.added', { ip: newIP }));
      setNewIP('');
      setNewIPDescription('');
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error: any) {
      console.error('Error adding IP:', error);
      setFormError(error.response?.data?.detail || t('ipWhitelist.errors.addFailed'));
      setTimeout(() => setFormError(''), 5000);
    }
  };

  const handleDeleteIP = async (ipId: number, ipAddress: string) => {
    if (!confirm(t('ipWhitelist.confirmDelete', { ip: ipAddress }))) {
      return;
    }

    try {
      await deleteIP(ipId);
      setSuccessMessage(t('ipWhitelist.success.removed', { ip: ipAddress }));
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error) {
      console.error('Error deleting IP:', error);
      setFormError(t('ipWhitelist.errors.deleteFailed'));
      setTimeout(() => setFormError(''), 3000);
    }
  };

  const handleToggleIPStatus = async (ipId: number, currentStatus: boolean) => {
    try {
      await updateWhitelistEntry(ipId, { is_active: !currentStatus });
      setSuccessMessage(t('ipWhitelist.success.statusUpdated'));
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error) {
      console.error('Error updating IP status:', error);
      setFormError(t('ipWhitelist.errors.updateFailed'));
      setTimeout(() => setFormError(''), 3000);
    }
  };

  const getSourceDisplayName = (sourceName: string): string => {
    return t(`dataSources.sources.${sourceName}`) as string;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gradient-cyan mb-8">{t('title')}</h1>
      </div>

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="mb-6 p-4 bg-status-safe/10 border border-status-safe/30 text-status-safe rounded">
          {successMessage}
        </div>
      )}
      {formError && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/30 text-destructive rounded">
          {formError}
        </div>
      )}

      {/* Data Sources Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-card-foreground mb-4">{t('dataSources.title')}</h2>
        <p className="text-muted-foreground mb-4">
          {t('dataSources.description')}
        </p>

        {loadingSources ? (
          <div className="bg-card shadow-glow border border-border rounded-lg p-6">
            <p className="text-muted-foreground">{t('dataSources.loading')}</p>
          </div>
        ) : (
          <div className="bg-card shadow-glow border border-border rounded-lg overflow-hidden">
            {sources.map((source) => (
              <div
                key={source.source_name}
                className="flex items-center justify-between p-6 border-b border-border last:border-b-0 hover:bg-muted/20 transition"
              >
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-card-foreground">
                    {getSourceDisplayName(source.source_name)}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">{source.description}</p>
                  {source.config_params && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <code className="bg-muted/50 px-2 py-1 rounded">
                        {JSON.stringify(source.config_params)}
                      </code>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleToggleSource(source.source_name, source.is_enabled)}
                  className={`ml-6 px-6 py-3 rounded-lg font-medium transition-colors ${
                    source.is_enabled
                      ? 'bg-status-safe text-white hover:bg-status-safe/90'
                      : 'bg-muted text-muted-foreground hover:bg-muted/70'
                  }`}
                >
                  {source.is_enabled ? t('dataSources.enabled') : t('dataSources.disabled')}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* IP Whitelist Section */}
      <section>
        <h2 className="text-2xl font-semibold text-card-foreground mb-4">
          {t('ipWhitelist.title')}
        </h2>
        <p className="text-muted-foreground mb-4">
          {t('ipWhitelist.description')}
        </p>

        {/* Add IP Form */}
        <div className="bg-card shadow-glow border border-border rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-card-foreground mb-4">{t('ipWhitelist.addNew')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder={t('ipWhitelist.ipPlaceholder')}
              value={newIP}
              onChange={(e) => setNewIP(e.target.value)}
              className="border border-border px-4 py-3 rounded-lg bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <input
              type="text"
              placeholder={t('ipWhitelist.descriptionPlaceholder')}
              value={newIPDescription}
              onChange={(e) => setNewIPDescription(e.target.value)}
              className="border border-border px-4 py-3 rounded-lg bg-background text-card-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={handleAddIP}
              className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
            >
              {t('ipWhitelist.addButton')}
            </button>
          </div>
        </div>

        {/* IP Whitelist Table */}
        {loadingWhitelist ? (
          <div className="bg-card shadow-glow border border-border rounded-lg p-6">
            <p className="text-muted-foreground">{t('ipWhitelist.loading')}</p>
          </div>
        ) : whitelist.length === 0 ? (
          <div className="bg-card shadow-glow border border-border rounded-lg p-6 text-center">
            <p className="text-muted-foreground">{t('ipWhitelist.noWhitelist')}</p>
          </div>
        ) : (
          <div className="bg-card shadow-glow border border-border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50 border-b border-border">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('ipWhitelist.table.ipAddress')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('ipWhitelist.table.description')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('ipWhitelist.table.status')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('ipWhitelist.table.createdAt')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t('ipWhitelist.table.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {whitelist.map((entry) => (
                  <tr key={entry.id} className="hover:bg-muted/10 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-sm font-mono text-card-foreground">{entry.ip_address}</code>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-card-foreground">
                        {entry.description || <span className="text-muted-foreground">-</span>}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleToggleIPStatus(entry.id, entry.is_active)}
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          entry.is_active
                            ? 'bg-status-safe/20 text-status-safe'
                            : 'bg-destructive/20 text-destructive'
                        }`}
                      >
                        {entry.is_active ? t('ipWhitelist.table.active') : t('ipWhitelist.table.inactive')}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground">
                      {new Date(entry.created_at).toLocaleString(locale)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleDeleteIP(entry.id, entry.ip_address)}
                        className="text-destructive hover:text-destructive/80 font-medium"
                      >
                        {t('ipWhitelist.table.delete')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
