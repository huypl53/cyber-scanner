'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ThreatData {
  timestamp: string;
  score: number;
  isAttack: boolean;
}

interface Props {
  data: ThreatData[];
}

export default function ThreatDetectionChart({ data }: Props) {
  const chartData = data.map((item, index) => ({
    index: index + 1,
    score: item.score,
    threshold: 0.5,
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Threat Detection Scores</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="index"
            label={{ value: 'Prediction #', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            domain={[0, 1]}
            label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#3b82f6"
            name="Threat Score"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="threshold"
            stroke="#ef4444"
            strokeDasharray="5 5"
            name="Threshold (0.5)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
