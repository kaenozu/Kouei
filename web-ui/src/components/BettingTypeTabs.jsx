import React, { useState, useEffect } from 'react';

const BETTING_TYPES = [
  { id: 'win', name: '単勝', icon: '🏆', description: '1着を当てる' },
  { id: 'place', name: '複勝', icon: '🎯', description: '3着以内を当てる' },
  { id: 'exacta', name: '2連単', icon: '⚡', description: '1-2着を順番通り' },
  { id: 'wide', name: 'ワイド', icon: '🎪', description: '3着以内の2艇' },
  { id: 'trifecta', name: '3連単', icon: '💎', description: '1-2-3着を順番通り' },
];

const API_BASE = '';

export default function BettingTypeTabs({ date }) {
  const [activeType, setActiveType] = useState('win');
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);

  useEffect(() => {
    fetchPredictions();
  }, [activeType, date]);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      const params = new URLSearchParams({ date: date || new Date().toISOString().slice(0, 10).replace(/-/g, '') });
      
      switch (activeType) {
        case 'win':
          endpoint = `/api/today?${params}`;
          break;
        case 'place':
          endpoint = `/api/place?${params}`;
          break;
        case 'exacta':
          endpoint = `/api/exacta?${params}`;
          break;
        case 'wide':
          endpoint = `/api/wide?${params}`;
          break;
        case 'trifecta':
          endpoint = `/api/trifecta?${params}`;
          break;
      }
      
      const res = await fetch(`${API_BASE}${endpoint}`);
      const data = await res.json();
      
      if (activeType === 'win') {
        setPredictions(data.races || []);
      } else {
        setPredictions(data.predictions || []);
      }
    } catch (err) {
      console.error('Error fetching predictions:', err);
      setPredictions([]);
    }
    setLoading(false);
  };

  const runBacktest = async () => {
    try {
      const endpoint = activeType === 'win' 
        ? `/api/backtest/comprehensive?strategy=win`
        : `/api/${activeType}/backtest`;
      
      const res = await fetch(`${API_BASE}${endpoint}`);
      const data = await res.json();
      setBacktestResult(data);
    } catch (err) {
      console.error('Backtest error:', err);
    }
  };

  const getConfidenceColor = (conf) => {
    switch (conf) {
      case 'S': return 'bg-yellow-500 text-black';
      case 'A': return 'bg-purple-500 text-white';
      case 'B': return 'bg-blue-500 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const renderPredictionCard = (pred, idx) => {
    if (activeType === 'win') {
      // Single win prediction format
      return (
        <div key={idx} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition">
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="text-gray-400 text-sm">{pred.jyo_name}</span>
              <span className="text-white font-bold ml-2">{pred.race_no}R</span>
            </div>
            <span className={`px-2 py-1 rounded text-xs font-bold ${getConfidenceColor(pred.confidence)}`}>
              {pred.confidence}ランク
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-3xl font-bold text-cyan-400">{pred.top_boat}号艇</div>
            <div className="text-xl text-green-400">{(pred.top_prob * 100).toFixed(1)}%</div>
          </div>
          {pred.start_time && (
            <div className="text-gray-500 text-sm mt-2">⏰ {pred.start_time}</div>
          )}
        </div>
      );
    }

    // Multi-boat predictions (exacta, trifecta, wide, place)
    return (
      <div key={idx} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition">
        <div className="flex justify-between items-start mb-2">
          <div>
            <span className="text-gray-400 text-sm">{pred.jyo_name}</span>
            <span className="text-white font-bold ml-2">{pred.race_no}R</span>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-bold ${getConfidenceColor(pred.confidence)}`}>
            {pred.confidence}
          </span>
        </div>
        
        <div className="flex items-center gap-2 mb-2">
          {activeType === 'place' ? (
            <span className="text-2xl font-bold text-cyan-400">{pred.boat_no}号艇</span>
          ) : activeType === 'wide' ? (
            <span className="text-2xl font-bold text-cyan-400">
              {pred.boat1}-{pred.boat2}
            </span>
          ) : activeType === 'exacta' ? (
            <span className="text-2xl font-bold text-cyan-400">
              {pred.first}→{pred.second}
            </span>
          ) : (
            <span className="text-2xl font-bold text-cyan-400">
              {pred.first}→{pred.second}→{pred.third}
            </span>
          )}
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <span className="text-gray-500">確率</span>
            <div className="text-green-400 font-bold">{(pred.probability * 100).toFixed(1)}%</div>
          </div>
          <div>
            <span className="text-gray-500">想定配当</span>
            <div className="text-yellow-400 font-bold">{pred.expected_odds?.toFixed(1)}倍</div>
          </div>
          <div>
            <span className="text-gray-500">期待値</span>
            <div className={`font-bold ${pred.ev >= 1.0 ? 'text-green-400' : 'text-red-400'}`}>
              {pred.ev?.toFixed(2)}
            </div>
          </div>
        </div>
        
        {pred.start_time && (
          <div className="text-gray-500 text-xs mt-2">⏰ {pred.start_time}</div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Betting Type Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {BETTING_TYPES.map((type) => (
          <button
            key={type.id}
            onClick={() => setActiveType(type.id)}
            className={`flex-shrink-0 px-4 py-2 rounded-lg font-medium transition ${
              activeType === type.id
                ? 'bg-cyan-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <span className="mr-1">{type.icon}</span>
            {type.name}
          </button>
        ))}
      </div>

      {/* Active Type Info */}
      <div className="bg-gray-800/50 rounded-lg p-3 flex justify-between items-center">
        <div>
          <span className="text-2xl mr-2">{BETTING_TYPES.find(t => t.id === activeType)?.icon}</span>
          <span className="text-lg font-bold text-white">
            {BETTING_TYPES.find(t => t.id === activeType)?.name}
          </span>
          <span className="text-gray-400 text-sm ml-2">
            {BETTING_TYPES.find(t => t.id === activeType)?.description}
          </span>
        </div>
        <button
          onClick={runBacktest}
          className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm"
        >
          バックテスト
        </button>
      </div>

      {/* Backtest Result */}
      {backtestResult && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-white font-bold mb-2">📊 バックテスト結果</h3>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-gray-400 text-sm">総賭け数</div>
              <div className="text-white font-bold">
                {backtestResult.summary?.total_bets || backtestResult.total_bets || 0}
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">的中数</div>
              <div className="text-green-400 font-bold">
                {backtestResult.summary?.total_wins || backtestResult.total_wins || 0}
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">的中率</div>
              <div className="text-cyan-400 font-bold">
                {backtestResult.summary?.hit_rate || backtestResult.hit_rate || 0}%
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-sm">ROI</div>
              <div className={`font-bold ${(backtestResult.summary?.roi || backtestResult.roi || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {backtestResult.summary?.roi || backtestResult.roi || 0}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Predictions Grid */}
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mx-auto"></div>
          <div className="text-gray-400 mt-2">読み込み中...</div>
        </div>
      ) : predictions.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          予測データがありません
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {predictions.slice(0, 20).map((pred, idx) => renderPredictionCard(pred, idx))}
        </div>
      )}
    </div>
  );
}
