'use client';

/**
 * POC Disclaimer Banner
 * Displays important notice about model accuracy limitations
 */
export default function POCDisclaimer() {
  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mb-6">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-amber-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-amber-800">
            Proof of Concept Mode
          </h3>
          <div className="mt-2 text-sm text-amber-700">
            <p>
              <strong>Demo/Development System:</strong> ML models trained on limited dataset (24 samples).
              Current threat detection accuracy is approximately 14%.
            </p>
            <p className="mt-1">
              <strong>Production Readiness:</strong> Requires retraining with 100,000+ samples to achieve
              industry-standard 90%+ accuracy. Infrastructure and data pipeline are production-ready.
            </p>
            <p className="mt-1 text-xs">
              <strong>⚠️ Do not enable automated self-healing actions in production until models achieve F1 score &gt; 0.95</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
