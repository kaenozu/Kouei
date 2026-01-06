import React, { useState } from 'react';
import { Brain, MessageSquare, TrendingUp, ChevronDown, ChevronUp, Award } from 'lucide-react';

const Card = ({ children, className = '' }) => (
  <div className={`bg-gray-800 border border-gray-700 rounded-lg ${className}`}>{children}</div>
);
const CardHeader = ({ children }) => <div className="p-4 border-b border-gray-700">{children}</div>;
const CardTitle = ({ children, className = '' }) => <h3 className={`text-lg font-semibold ${className}`}>{children}</h3>;
const CardContent = ({ children }) => <div className="p-4">{children}</div>;

const ConfidenceBadge = ({ confidence }) => {
  const colors = {
    'S': 'bg-red-600',
    'A': 'bg-orange-500',
    'B': 'bg-yellow-500',
    'C': 'bg-gray-500'
  };
  return (
    <span className={`px-3 py-1 rounded-full text-white font-bold ${colors[confidence] || 'bg-gray-500'}`}>
      {confidence}ランク
    </span>
  );
};

const BoatNumberBadge = ({ number }) => {
  const colors = {
    1: 'bg-white text-black',
    2: 'bg-black text-white',
    3: 'bg-red-600 text-white',
    4: 'bg-blue-600 text-white',
    5: 'bg-yellow-400 text-black',
    6: 'bg-green-600 text-white'
  };
  return (
    <span className={`w-8 h-8 flex items-center justify-center rounded-full font-bold ${colors[number] || 'bg-gray-500'}`}>
      {number}
    </span>
  );
};

const PredictionExplainer = ({ predictions = [], raceInfo = {} }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  
  const fetchExplanation = async () => {
    if (loading) return;
    setLoading(true);
    
    try {
      const response = await fetch('/api/explain/race', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          predictions: predictions,
          race_info: raceInfo,
          include_shap: false
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setExplanation(data);
        setExpanded(true);
      } else {
        console.error('Failed to fetch explanation');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (predictions.length === 0) {
    return null;
  }
  
  return (
    <Card className="mt-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-500" />
            AI予測解説
          </CardTitle>
          <button
            onClick={explanation ? () => setExpanded(!expanded) : fetchExplanation}
            className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition"
            disabled={loading}
          >
            {loading ? (
              <span className="animate-spin">⏳</span>
            ) : explanation ? (
              expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
            ) : (
              <MessageSquare className="w-4 h-4" />
            )}
            {explanation ? (expanded ? '閉じる' : '展開') : '解説を見る'}
          </button>
        </div>
      </CardHeader>
      
      {expanded && explanation && (
        <CardContent>
          {/* Summary */}
          <div className="mb-4 p-4 bg-gray-900 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">総合評価</span>
              <ConfidenceBadge confidence={explanation.confidence} />
            </div>
            <p className="text-lg font-medium">{explanation.summary}</p>
          </div>
          
          {/* Top predictions with explanations */}
          <div className="space-y-3">
            {explanation.predictions?.map((pred, index) => (
              <div 
                key={pred.boat_no}
                className={`p-3 rounded-lg border ${
                  index === 0 
                    ? 'border-yellow-500 bg-yellow-500/10' 
                    : 'border-gray-700 bg-gray-900'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  {index === 0 && <Award className="w-5 h-5 text-yellow-500" />}
                  <BoatNumberBadge number={pred.boat_no} />
                  <span className="font-semibold">{pred.racer_name}</span>
                  <span className="ml-auto text-blue-400 font-bold">
                    {(pred.probability * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm text-gray-300 pl-11">{pred.explanation}</p>
                
                {/* Top factors */}
                {pred.top_factors && pred.top_factors.length > 0 && (
                  <div className="mt-2 pl-11 flex flex-wrap gap-2">
                    {pred.top_factors.map((factor, i) => (
                      <span 
                        key={i}
                        className={`text-xs px-2 py-1 rounded ${
                          factor.impact > 0 
                            ? 'bg-green-900 text-green-300' 
                            : 'bg-red-900 text-red-300'
                        }`}
                      >
                        {factor.feature}: {factor.impact > 0 ? '+' : ''}{(factor.impact * 100).toFixed(1)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <p className="mt-4 text-xs text-gray-500 text-right">
            Generated at: {explanation.generated_at}
          </p>
        </CardContent>
      )}
    </Card>
  );
};

export default PredictionExplainer;
