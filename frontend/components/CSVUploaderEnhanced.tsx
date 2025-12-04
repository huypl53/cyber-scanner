'use client';

import { useState } from 'react';
import { uploadCSV } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import Link from 'next/link';
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
  TrendingUp,
} from 'lucide-react';

type UploadStep = 'parsing' | 'normalizing' | 'analyzing' | 'classifying' | 'complete';

const steps = [
  { key: 'parsing', label: 'Parsing CSV', icon: File },
  { key: 'normalizing', label: 'Normalizing Data', icon: FileCheck },
  { key: 'analyzing', label: 'Running AI Models', icon: Loader2 },
  { key: 'classifying', label: 'Classifying Threats', icon: AlertTriangle },
  { key: 'complete', label: 'Complete', icon: CheckCircle2 },
];

export default function CSVUploaderEnhanced() {
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

  const simulateProgress = async () => {
    const stepDurations = {
      parsing: 1000,
      normalizing: 1500,
      analyzing: 2000,
      classifying: 1500,
      complete: 500,
    };

    for (const step of steps) {
      setCurrentStep(step.key as UploadStep);
      const duration = stepDurations[step.key as keyof typeof stepDurations];
      const stepIndex = steps.findIndex((s) => s.key === step.key);
      const startProgress = (stepIndex / steps.length) * 100;
      const endProgress = ((stepIndex + 1) / steps.length) * 100;

      // Animate progress within this step
      const frames = 20;
      for (let i = 0; i <= frames; i++) {
        await new Promise((resolve) => setTimeout(resolve, duration / frames));
        const stepProgress = startProgress + (endProgress - startProgress) * (i / frames);
        setProgress(stepProgress);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    setUploading(true);
    setError(null);
    setProgress(0);
    setCurrentStep('parsing');

    try {
      // Start progress simulation
      const progressPromise = simulateProgress();

      // Upload file
      const response = await uploadCSV(file);

      // Wait for progress to complete
      await progressPromise;

      setResult(response);
      setFile(null);

      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
      setCurrentStep(null);
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const attacksCount = result?.predictions.filter((p: any) =>
    p.threat_prediction?.is_attack || p.attack_prediction
  ).length || 0;

  const normalCount = result?.predictions.filter((p: any) =>
    p.threat_prediction && !p.threat_prediction.is_attack && !p.attack_prediction
  ).length || 0;

  const attackRate = result ? (attacksCount / result.total_rows) * 100 : 0;

  return (
    <div className="w-full space-y-6">
      <Card className="shadow-glow">
        <CardContent className="p-6">
          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
              'relative border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300',
              isDragging
                ? 'border-primary bg-primary/10 scale-105'
                : 'border-border hover:border-primary/50',
              'cursor-pointer group'
            )}
          >
            <input
              id="file-upload"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="flex flex-col items-center space-y-4">
                <div
                  className={cn(
                    'p-4 rounded-full transition-all duration-300',
                    isDragging
                      ? 'bg-primary/20 scale-110'
                      : 'bg-muted group-hover:bg-primary/10'
                  )}
                >
                  <Upload
                    className={cn(
                      'h-12 w-12 transition-colors',
                      isDragging ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'
                    )}
                  />
                </div>
                <div>
                  <p className="text-lg font-semibold mb-1">
                    <span className="text-primary">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-sm text-muted-foreground">
                    CSV files with network traffic data
                  </p>
                </div>
              </div>
            </label>

            {/* Animated border */}
            {isDragging && (
              <div className="absolute inset-0 rounded-lg border-2 border-primary animate-pulse-glow" />
            )}
          </div>

          {/* Selected File */}
          {file && !uploading && (
            <Card className="mt-4 bg-primary/10 border-primary/20 animate-fade-in">
              <CardContent className="p-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <File className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFile(null)}
                  className="text-destructive hover:text-destructive hover:bg-destructive/10"
                >
                  <X className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="mt-4 w-full shadow-glow"
            size="lg"
          >
            {uploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload and Analyze
              </>
            )}
          </Button>

          {/* Progress Steps */}
          {uploading && currentStep && (
            <div className="mt-6 space-y-4 animate-fade-in">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">
                    {steps.find((s) => s.key === currentStep)?.label}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {Math.round(progress)}%
                  </span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>

              <div className="grid grid-cols-5 gap-2">
                {steps.map((step, index) => {
                  const Icon = step.icon;
                  const stepIndex = steps.findIndex((s) => s.key === currentStep);
                  const isActive = step.key === currentStep;
                  const isComplete = index < stepIndex;

                  return (
                    <div key={step.key} className="flex flex-col items-center gap-2">
                      <div
                        className={cn(
                          'p-3 rounded-full transition-all duration-300',
                          isActive && 'bg-primary/20 shadow-glow',
                          isComplete && 'bg-status-safe/20',
                          !isActive && !isComplete && 'bg-muted'
                        )}
                      >
                        <Icon
                          className={cn(
                            'h-5 w-5 transition-colors',
                            isActive && 'text-primary animate-pulse',
                            isComplete && 'text-status-safe',
                            !isActive && !isComplete && 'text-muted-foreground'
                          )}
                        />
                      </div>
                      <p
                        className={cn(
                          'text-xs text-center transition-colors',
                          isActive && 'text-primary font-semibold',
                          isComplete && 'text-status-safe',
                          !isActive && !isComplete && 'text-muted-foreground'
                        )}
                      >
                        {step.label}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <Card className="mt-4 bg-destructive/10 border-destructive/20 animate-fade-in">
              <CardContent className="p-4 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-destructive mb-1">Upload Failed</h4>
                  <p className="text-sm text-destructive/90">{error}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Success Result */}
          {result && !uploading && (
            <Card className="mt-4 bg-status-safe/10 border-status-safe/20 animate-fade-in">
              <CardContent className="p-6 space-y-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-status-safe/20 rounded-full">
                    <CheckCircle2 className="h-8 w-8 text-status-safe" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-status-safe">
                      Analysis Complete!
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Processed {result.total_rows.toLocaleString()} network traffic records
                    </p>
                  </div>
                  <Badge variant="outline" className="font-mono">
                    ID: {result.batch_id}
                  </Badge>
                </div>

                {/* Summary Stats with Donut */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="bg-destructive/10 border-destructive/20">
                    <CardContent className="p-4 text-center">
                      <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-destructive" />
                      <p className="text-sm text-muted-foreground mb-1">Attacks Detected</p>
                      <p className="text-3xl font-bold text-destructive">
                        {attacksCount.toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {attackRate.toFixed(1)}% of total
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="bg-status-safe/10 border-status-safe/20">
                    <CardContent className="p-4 text-center">
                      <Shield className="h-8 w-8 mx-auto mb-2 text-status-safe" />
                      <p className="text-sm text-muted-foreground mb-1">Normal Traffic</p>
                      <p className="text-3xl font-bold text-status-safe">
                        {normalCount.toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {(100 - attackRate).toFixed(1)}% of total
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="bg-primary/10 border-primary/20">
                    <CardContent className="p-4 text-center">
                      <PieChart className="h-8 w-8 mx-auto mb-2 text-primary" />
                      <p className="text-sm text-muted-foreground mb-1">Total Records</p>
                      <p className="text-3xl font-bold text-primary">
                        {result.total_rows.toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Batch processed
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* View Dashboard Button */}
                <Link href="/dashboard">
                  <Button className="w-full shadow-glow" size="lg">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    View Full Analysis
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
