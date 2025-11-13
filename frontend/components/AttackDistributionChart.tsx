'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface Props {
  distribution: Record<string, number>;
}

const COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7'
];

export default function AttackDistributionChart({ distribution }: Props) {
  const chartData = Object.entries(distribution).map(([name, count]) => ({
    name: name.length > 20 ? name.substring(0, 20) + '...' : name,
    fullName: name,
    count,
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Attack Type Distribution</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
          />
          <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-2 border border-gray-300 rounded shadow">
                    <p className="font-semibold">{payload[0].payload.fullName}</p>
                    <p>Count: {payload[0].value}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar dataKey="count" name="Attack Count">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
