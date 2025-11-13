'use client';

import { CompletePrediction } from '@/lib/api';

interface Props {
  predictions: CompletePrediction[];
}

export default function PredictionHistoryTable({ predictions }: Props) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Recent Predictions</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Threat Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Attack Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Confidence
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {predictions.map((pred) => (
              <tr key={pred.traffic_data.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(pred.threat_prediction.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {pred.threat_prediction.prediction_score.toFixed(3)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    pred.threat_prediction.is_attack
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {pred.threat_prediction.is_attack ? 'Attack' : 'Normal'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {pred.attack_prediction?.attack_type_name || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {pred.attack_prediction?.confidence
                    ? `${(pred.attack_prediction.confidence * 100).toFixed(1)}%`
                    : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {predictions.length === 0 && (
          <p className="text-center text-gray-500 py-8">No predictions yet</p>
        )}
      </div>
    </div>
  );
}
