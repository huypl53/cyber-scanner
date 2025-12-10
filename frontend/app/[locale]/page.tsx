import { useTranslations } from 'next-intl';
import CSVUploaderEnhanced from '@/components/CSVUploaderEnhanced';
import { Card, CardContent } from '@/components/ui/card';
import { Shield, Target, Zap, Database, Lock } from 'lucide-react';

export default function Home() {
  const t = useTranslations('home');

  const features = [
    {
      icon: Shield,
      titleKey: 'features.binaryThreat.title',
      descriptionKey: 'features.binaryThreat.description',
      color: 'text-primary',
      bg: 'bg-primary/10',
    },
    {
      icon: Target,
      titleKey: 'features.multiClass.title',
      descriptionKey: 'features.multiClass.description',
      color: 'text-destructive',
      bg: 'bg-destructive/10',
    },
    {
      icon: Zap,
      titleKey: 'features.selfHealing.title',
      descriptionKey: 'features.selfHealing.description',
      color: 'text-status-warning',
      bg: 'bg-amber-500/10',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gradient-cyan mb-2">
          {t('title')}
        </h1>
        <p className="text-muted-foreground">
          {t('subtitle')}
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
              key={feature.titleKey}
              className="shadow-glow hover:scale-105 transition-transform duration-300"
            >
              <CardContent className="p-6">
                <div
                  className={`inline-flex p-3 rounded-lg ${feature.bg} mb-4`}
                >
                  <Icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="font-semibold text-lg mb-2">{t(feature.titleKey)}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {t(feature.descriptionKey)}
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
            {t('capabilities.title')}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-1">{t('capabilities.realtimeAnalysis')}</p>
              <p className="text-2xl font-bold text-primary">{t('capabilities.realtimeValue')}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-1">{t('capabilities.protocols')}</p>
              <p className="text-2xl font-bold text-primary">{t('capabilities.protocolsValue')}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-1">{t('capabilities.accuracy')}</p>
              <p className="text-2xl font-bold text-primary">{t('capabilities.accuracyValue')}</p>
            </div>
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
            <h4 className="font-semibold mb-1">{t('security.title')}</h4>
            <p className="text-sm text-muted-foreground">
              {t('security.description')}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
