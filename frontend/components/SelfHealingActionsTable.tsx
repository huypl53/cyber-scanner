'use client';

import { SelfHealingAction } from '@/lib/api';

interface Props {
  actions: SelfHealingAction[];
}

const actionTypeColors: Record<string, string> = {
  'restart_service': 'bg-blue-100 text-blue-800',
  'block_ip': 'bg-red-100 text-red-800',
  'alert_admin': 'bg-yellow-100 text-yellow-800',
  'log_only': 'bg-gray-100 text-gray-800',
};

export default function SelfHealingActionsTable({ actions }: Props) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Self-Healing Actions</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {actions.map((action) => (
              <tr key={action.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(action.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    actionTypeColors[action.action_type] || 'bg-gray-100 text-gray-800'
                  }`}>
                    {action.action_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {action.action_description}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {action.status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {actions.length === 0 && (
          <p className="text-center text-gray-500 py-8">No actions logged yet</p>
        )}
      </div>
    </div>
  );
}
