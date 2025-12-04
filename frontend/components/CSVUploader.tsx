'use client';

import { useState } from 'react';
import { uploadCSV } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import {
  Upload,
  File,
  FileCheck,
  AlertTriangle,
  Shield,
  CheckCircle2,
  X,
  Loader2,
  PieChart,
} from 'lucide-react';

type UploadStep = 'parsing' | 'normalizing' | 'analyzing' | 'classifying' | 'complete';

export default function CSVUploader() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState<UploadStep | null>(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const response = await uploadCSV(file);
      setResult(response);
      setFile(null);

      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div className="w-full">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Upload Network Traffic Data</h2>

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer"
        >
          <input
            id="file-upload"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="mt-4 text-sm text-gray-600">
              <span className="font-semibold text-blue-600 hover:text-blue-500">
                Click to upload
              </span>{' '}
              or drag and drop
            </div>
            <p className="text-xs text-gray-500 mt-1">CSV files only</p>
          </label>
        </div>

        {/* Selected File */}
        {file && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg flex justify-between items-center">
            <div>
              <p className="font-medium text-blue-900">{file.name}</p>
              <p className="text-sm text-blue-700">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
            <button
              onClick={() => setFile(null)}
              className="text-red-600 hover:text-red-800"
            >
              Remove
            </button>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {uploading ? 'Uploading...' : 'Upload and Analyze'}
        </button>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Success Result */}
        {result && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-bold text-green-900 mb-2">Upload Successful!</h3>
            <p className="text-green-800">
              Processed {result.total_rows} rows
            </p>
            <p className="text-sm text-green-700 mt-1">
              Batch ID: {result.batch_id}
            </p>

            {/* Summary Stats */}
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="bg-white p-3 rounded">
                <p className="text-sm text-gray-600">Attacks Detected</p>
                <p className="text-2xl font-bold text-red-600">
                  {result.predictions.filter((p: any) =>
                    p.threat_prediction?.is_attack || p.attack_prediction
                  ).length}
                </p>
              </div>
              <div className="bg-white p-3 rounded">
                <p className="text-sm text-gray-600">Normal Traffic</p>
                <p className="text-2xl font-bold text-green-600">
                  {result.predictions.filter((p: any) =>
                    p.threat_prediction && !p.threat_prediction.is_attack && !p.attack_prediction
                  ).length}
                </p>
              </div>
            </div>

            {/* View Details Button */}
            <a
              href="/dashboard"
              className="mt-4 block w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 text-center"
            >
              View Dashboard
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
