'use client';

import { useState, useEffect } from 'react';
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
      setFormError('Failed to load settings');
    } finally {
      setLoadingSources(false);
      setLoadingWhitelist(false);
    }
  };

  const handleToggleSource = async (sourceName: string, currentStatus: boolean) => {
    try {
      await updateDataSource(sourceName, { is_enabled: !currentStatus });
      setSuccessMessage(`${sourceName} ${!currentStatus ? 'enabled' : 'disabled'} successfully`);
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error) {
      console.error('Error toggling source:', error);
      setFormError(`Failed to toggle ${sourceName}`);
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
      setFormError('IP address is required');
      return;
    }

    if (!validateIP(newIP)) {
      setFormError('Invalid IP address format (must be IPv4, e.g., 192.168.1.100)');
      return;
    }

    try {
      await addIPToWhitelist({
        ip_address: newIP,
        description: newIPDescription || undefined,
        is_active: true,
      });

      setSuccessMessage(`IP ${newIP} added to whitelist`);
      setNewIP('');
      setNewIPDescription('');
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error: any) {
      console.error('Error adding IP:', error);
      setFormError(error.response?.data?.detail || 'Failed to add IP to whitelist');
      setTimeout(() => setFormError(''), 5000);
    }
  };

  const handleDeleteIP = async (ipId: number, ipAddress: string) => {
    if (!confirm(`Are you sure you want to remove ${ipAddress} from the whitelist?`)) {
      return;
    }

    try {
      await deleteIP(ipId);
      setSuccessMessage(`IP ${ipAddress} removed from whitelist`);
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error) {
      console.error('Error deleting IP:', error);
      setFormError('Failed to delete IP from whitelist');
      setTimeout(() => setFormError(''), 3000);
    }
  };

  const handleToggleIPStatus = async (ipId: number, currentStatus: boolean) => {
    try {
      await updateWhitelistEntry(ipId, { is_active: !currentStatus });
      setSuccessMessage('IP status updated');
      setTimeout(() => setSuccessMessage(''), 3000);
      await loadSettings();
    } catch (error) {
      console.error('Error updating IP status:', error);
      setFormError('Failed to update IP status');
      setTimeout(() => setFormError(''), 3000);
    }
  };

  const getSourceDisplayName = (sourceName: string): string => {
    const names: Record<string, string> = {
      packet_capture: 'Packet Capture',
      external_kafka: 'External Kafka Stream',
      internal_kafka: 'Internal Kafka Stream',
    };
    return names[sourceName] || sourceName;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Settings</h1>

        {/* Success/Error Messages */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            {successMessage}
          </div>
        )}
        {formError && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {formError}
          </div>
        )}

        {/* Data Sources Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Data Sources</h2>
          <p className="text-gray-600 mb-4">
            Enable or disable data collection sources. Multiple sources can run simultaneously.
          </p>

          {loadingSources ? (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-500">Loading data sources...</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {sources.map((source) => (
                <div
                  key={source.source_name}
                  className="flex items-center justify-between p-6 border-b last:border-b-0 hover:bg-gray-50 transition"
                >
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900">
                      {getSourceDisplayName(source.source_name)}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                    {source.config_params && (
                      <div className="mt-2 text-xs text-gray-500">
                        <code className="bg-gray-100 px-2 py-1 rounded">
                          {JSON.stringify(source.config_params)}
                        </code>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => handleToggleSource(source.source_name, source.is_enabled)}
                    className={`ml-6 px-6 py-3 rounded-lg font-medium transition-colors ${
                      source.is_enabled
                        ? 'bg-green-500 text-white hover:bg-green-600'
                        : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                    }`}
                  >
                    {source.is_enabled ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* IP Whitelist Section */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            IP Whitelist (External Data Providers)
          </h2>
          <p className="text-gray-600 mb-4">
            Manage IP addresses allowed to send data via the external Kafka stream. Only
            whitelisted IPs can send traffic data for analysis.
          </p>

          {/* Add IP Form */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add New IP Address</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input
                type="text"
                placeholder="IP Address (e.g., 192.168.1.100)"
                value={newIP}
                onChange={(e) => setNewIP(e.target.value)}
                className="border border-gray-300 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="text"
                placeholder="Description (optional)"
                value={newIPDescription}
                onChange={(e) => setNewIPDescription(e.target.value)}
                className="border border-gray-300 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddIP}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
              >
                Add IP
              </button>
            </div>
          </div>

          {/* IP Whitelist Table */}
          {loadingWhitelist ? (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-500">Loading whitelist...</p>
            </div>
          ) : whitelist.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-500">No whitelisted IPs yet. Add one above to get started.</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      IP Address
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Created At
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {whitelist.map((entry) => (
                    <tr key={entry.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <code className="text-sm font-mono text-gray-900">{entry.ip_address}</code>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-700">
                          {entry.description || <span className="text-gray-400">-</span>}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleToggleIPStatus(entry.id, entry.is_active)}
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            entry.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {entry.is_active ? 'Active' : 'Inactive'}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleDeleteIP(entry.id, entry.ip_address)}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          Delete
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
    </div>
  );
}
