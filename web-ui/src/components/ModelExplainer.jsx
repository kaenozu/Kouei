import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, TrendingUp, Info } from 'lucide-react';

const ModelExplainer = () => {
  const [featureImportance, setFeatureImportance] = useState([]);
  const [modelComparison, setModelComparison] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState('ensemble');

  useEffect(() => {
    fetchFeatureImportance();
    fetchModelComparison();
  }, [selectedModel]);

  const fetchFeatureImportance = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/model-explain/feature-importance/${selectedModel}`);
      const data = await response.json();
      setFeatureImportance(data.features);
    } catch (error) {
      console.error('Error fetching feature importance:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchModelComparison = async () => {
    try {
      const response = await fetch('/api/v1/model-explain/model-comparison');
      const data = await response.json();
      setModelComparison(data.models);
    } catch (error) {
      console.error('Error fetching model comparison:', error);
    }
  };

  const models = ['ensemble', 'lightgbm', 'catboost', 'xgboost', 'neural-network'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">モデル解釈（Model Explainability）</h2>
        <div className="flex gap-2">
          {models.map(model => (
            <Button
              key={model}
              variant={selectedModel === model ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedModel(model)}
              className="capitalize"
            >
              {model}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feature Importance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              特徴量重要度
            </CardTitle>
            <CardDescription>
              {selectedModel}モデルの予測に最も影響のある特徴量
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="space-y-1">
                    <div className="h-4 bg-gray-200 rounded animate-pulse" />
                    <div className="h-2 bg-gray-200 rounded animate-pulse w-2/3" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {featureImportance.slice(0, 10).map((feature, index) => (
                  <div key={feature.name} className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        {index + 1}. {feature.name}
                      </span>
                      <Badge variant="secondary">
                        {feature.importance.toFixed(4)}
                      </Badge>
                    </div>
                    <Progress 
                      value={(feature.importance / Math.max(...featureImportance.map(f => f.importance))) * 100} 
                      className="h-2"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="w-5 h-5" />
              モデルパフォーマンス比較
            </CardTitle>
            <CardDescription>
              各モデルの性能メトリクス比較
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {modelComparison.map(model => (
                <div key={model.name} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{model.name}</span>
                    <Badge 
                      variant={model.name === 'Ensemble' ? 'default' : 'secondary'}
                    >
                      {model.name === 'Ensemble' ? '推奨' : ''}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex justify-between">
                      <span>AUC:</span>
                      <span className="font-mono">{model.auc.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>精度:</span>
                      <span className="font-mono">{(model.accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>1着率:</span>
                      <span className="font-mono">{(model.hit_rate_top1 * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>学習時間:</span>
                      <span className="font-mono">{model.training_time_min.toFixed(1)}分</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            モデル解釈の重要性
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold text-blue-600">予測の信頼性</h3>
              <p className="text-sm text-gray-600">
                特徴量の寄与度を明らかにし、なぜ特定の予測が出たのかを理解できます
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-green-600">モデル改善</h3>
              <p className="text-sm text-gray-600">
                重要な特徴量を特定し、データ収集や特徴エンジニアリングの重点を決定できます
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-purple-600">リスク管理</h3>
              <p className="text-sm text-gray-600">
                モデルの判断根拠を可視化し、予測結果の信頼性を評価しやすくなります
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelExplainer;