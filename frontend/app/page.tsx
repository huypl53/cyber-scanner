import CSVUploader from '@/components/CSVUploader';

export default function Home() {
  return (
    <div className="px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Network Traffic Analysis
        </h1>
        <p className="mt-2 text-gray-600">
          Upload CSV files containing network traffic data for threat detection and attack classification
        </p>
      </div>

      <CSVUploader />

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-2">Threat Detection</h3>
          <p className="text-gray-600 text-sm">
            Binary classification using ensemble model (ANN + LSTM) to detect attacks vs normal traffic
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-2">Attack Classification</h3>
          <p className="text-gray-600 text-sm">
            Multi-class classification identifying 14 attack types including DDoS, PortScan, and more
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-2">Self-Healing Actions</h3>
          <p className="text-gray-600 text-sm">
            Automated response suggestions including service restarts, IP blocking, and admin alerts
          </p>
        </div>
      </div>
    </div>
  );
}
