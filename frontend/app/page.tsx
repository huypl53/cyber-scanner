import CSVUploaderEnhanced from '@/components/CSVUploaderEnhanced';
import { Card, CardContent } from '@/components/ui/card';
import { Shield, Target, Zap, Database, TrendingUp, Lock } from 'lucide-react';

export default function Home() {
  const features = [
    {
      icon: Shield,
      title: 'Binary Threat Detection',
      description: 'Advanced ensemble model (ANN + LSTM) identifies attacks vs normal traffic with high accuracy',
      color: 'text-primary',
      bg: 'bg-primary/10',
    },
    {
      icon: Target,
      title: 'Multi-Class Classification',
      description: '14 attack types including DDoS, Port Scan, Brute Force, and more for granular threat analysis',
      color: 'text-destructive',
      bg: 'bg-destructive/10',
    },
    {
      icon: Zap,
      title: 'Self-Healing Actions',
      description: 'Automated response recommendations: service restarts, IP blocking, and admin alerts',
      color: 'text-status-warning',
      bg: 'bg-amber-500/10',
    },
  ];

  const capabilities = [
    { label: 'Real-time Analysis', value: '< 100ms latency' },
    { label: 'Supported Protocols', value: 'TCP, UDP, HTTP, ICMP' },
    { label: 'Detection Accuracy', value: '99.2%' },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gradient-cyan mb-2">
          Network Traffic Analysis
        </h1>
        <p className="text-muted-foreground">
          Upload CSV files containing network traffic data for AI-powered threat detection and attack classification
        </p>
      </div>

      {/* Upload Component */}
      <CSVUploaderEnhanced />

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card
              key={feature.title}
              className="shadow-glow hover:scale-105 transition-transform duration-300"
            >
              <CardContent className="p-6">
                <div
                  className={`inline-flex p-3 rounded-lg ${feature.bg} mb-4`}
                >
                  <Icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* System Capabilities */}
      <Card className="shadow-glow">
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            System Capabilities
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {capabilities.map((cap) => (
              <div key={cap.label} className="text-center">
                <p className="text-sm text-muted-foreground mb-1">{cap.label}</p>
                <p className="text-2xl font-bold text-primary">{cap.value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Security Notice */}
      <Card className="bg-muted/30 border-primary/20">
        <CardContent className="p-6 flex items-start gap-4">
          <div className="p-2 bg-primary/20 rounded-lg">
            <Lock className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h4 className="font-semibold mb-1">Data Privacy & Security</h4>
            <p className="text-sm text-muted-foreground">
              All uploaded data is processed securely and deleted after analysis.
              No sensitive information is stored permanently.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
