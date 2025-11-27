'use client';

import { useState, useCallback } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { startTestStream } from '@/lib/api';

interface RealtimePrediction {
  timestamp: string;
  traffic_data_id: number;
  threat_prediction: {
    prediction_score: number;
    is_attack: boolean;
    threshold: number;
  } | null;
  attack_prediction?: {
    attack_type_name: string;
    confidence: number;
  };
  self_healing_action?: {
    action_type: string;
    action_description: string;
  };
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export default function RealtimePage() {
  const [predictions, setPredictions] = useState<RealtimePrediction[]>([]);
  const [streamActive, setStreamActive] = useState(false);

  const handleMessage = useCallback((message: any) => {
    if (message.type === 'prediction') {
      setPredictions((prev) => [message.data, ...prev].slice(0, 50));
    }
  }, []);

  const { isConnected } = useWebSocket({
    url: `${WS_URL}/ws/realtime`,
    onMessage: handleMessage,
  });

  const handleStartStream = async () => {
    try {
      setStreamActive(true);
      await startTestStream({
        count: 100,
        interval: 1.0,
        model_type: 'attack_classification',
      });
    } catch (error) {
      console.error('Failed to start stream:', error);
    } finally {
      setTimeout(() => setStreamActive(false), 5000);
    }
  };

  const stats = {
    total: predictions.length,
    attacks: predictions.filter((p) => p.threat_prediction?.is_attack).length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Real-time Monitoring</h1>
          <p className="text-gray-600 mt-1">Live threat detection and attack classification</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center">
            <div
              className={`w-3 h-3 rounded-full mr-2 ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <button
            onClick={handleStartStream}
            disabled={streamActive || !isConnected}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {streamActive ? 'Stream Active...' : 'Start Test Stream'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Total Received</p>
          <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Attacks Detected</p>
          <p className="text-3xl font-bold text-red-600">{stats.attacks}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-sm text-gray-600 mb-1">Normal Traffic</p>
          <p className="text-3xl font-bold text-green-600">{stats.total - stats.attacks}</p>
        </div>
      </div>

      {/* Real-time Feed */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Live Predictions</h2>
        </div>
        <div className="max-h-[600px] overflow-y-auto">
          {predictions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>Waiting for real-time data...</p>
              <p className="text-sm mt-2">Click "Start Test Stream" to generate sample traffic</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {predictions.map((pred, index) => (
                <div
                  key={index}
                  className={`p-4 ${
                    pred.threat_prediction?.is_attack || pred.attack_prediction ? 'bg-red-50' : 'bg-green-50'
                  } hover:opacity-75 transition-opacity`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            pred.threat_prediction?.is_attack || pred.attack_prediction
                              ? 'bg-red-600 text-white'
                              : 'bg-green-600 text-white'
                          }`}
                        >
                          {pred.threat_prediction?.is_attack || pred.attack_prediction ? 'ATTACK' : 'NORMAL'}
                        </span>
                        <span className="text-sm text-gray-600">
                          {new Date(pred.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-sm space-y-1">
                        {pred.threat_prediction && (
                          <p>
                            <span className="font-medium">Threat Score:</span>{' '}
                            {pred.threat_prediction.prediction_score.toFixed(3)}
                          </p>
                        )}
                        {pred.attack_prediction && (
                          <>
                            <p>
                              <span className="font-medium">Attack Type:</span>{' '}
                              {pred.attack_prediction.attack_type_name}
                            </p>
                            <p>
                              <span className="font-medium">Confidence:</span>{' '}
                              {(pred.attack_prediction.confidence * 100).toFixed(1)}%
                            </p>
                          </>
                        )}
                        {pred.self_healing_action && (
                          <p className="text-orange-700">
                            <span className="font-medium">Action:</span>{' '}
                            {pred.self_healing_action.action_description}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
