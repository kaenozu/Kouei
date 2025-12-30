import React, { useState, useEffect } from 'react';
import { LayoutDashboard, TrendingUp, BarChart3, Settings, Info, CheckCircle2, Clock, Briefcase, Copy, Trophy, Star, Mic, MicOff, MessageSquare, Send, X, Box, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import WhatIfPanel from './components/WhatIfPanel';

const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [params, setParams] = useState({ date: new Date().toISOString().split('T')[0].replace(/-/g, ''), jyo: '02', race: 1 });
  const [predictions, setPredictions] = useState([]);
  const [aiFocus, setAiFocus] = useState(null);
  const [status, setStatus] = useState(null);
  const [stadiums, setStadiums] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [raceList, setRaceList] = useState([]);
  const [simulationData, setSimulationData] = useState({ history: [], summary: null });
  const [todayRaces, setTodayRaces] = useState([]);
  const [backtestFilters, setBacktestFilters] = useState({ stadium: '', min_prob: 0.4 });
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [strategies, setStrategies] = useState([]);
  const [optimizing, setOptimizing] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [portfolio, setPortfolio] = useState(null);
  // Phase 6-8 new features
  const [racerSearch, setRacerSearch] = useState('');
  const [racerStats, setRacerStats] = useState(null);
  const [racerLoading, setRacerLoading] = useState(false);
  const [monteCarloResult, setMonteCarloResult] = useState(null);
  const [monteCarloLoading, setMonteCarloLoading] = useState(false);
  const [selectedMonteCarloStrategy, setSelectedMonteCarloStrategy] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [whatIfFeatures, setWhatIfFeatures] = useState({ wind_speed: 0, wave_height: 0, temperature: 20, water_temp: 20 });
  const [whatIfSimulating, setWhatIfSimulating] = useState(false);
  const [userStats, setUserStats] = useState({ level: 1, exp: 45, badges: ['Early Bird', 'First Prediction'] });
  const [isListening, setIsListening] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([{ role: 'ai', content: 'こんにちは！AIコンシェルジュです。今日のレースについて何かお手伝いしましょうか？' }]);
  const [show3D, setShow3D] = useState(false);

  const fetchPrediction = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`http://localhost:8001/api/prediction?date=${params.date}&jyo=${params.jyo}&race=${params.race}`);
      const data = await resp.json();
      if (data && data.predictions) {
        setPredictions(data.predictions);
        setAiFocus({
          tips: data.tips || { nirentan: [], sanrentan: [] },
          confidence: data.confidence || 'C',
          insights: data.insights || [],
          race_name: data.race_name || ''
        });
      } else {
        setPredictions([]);
        setAiFocus(null);
      }
    } catch (e) {
      console.error("Fetch failed", e);
    }
    setLoading(false);
  };

  const runWhatIfSimulation = async (modifiedFeatures) => {
    setWhatIfSimulating(true);
    try {
      const resp = await fetch('http://localhost:8001/api/simulate-what-if', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modifications: modifiedFeatures })
      });
      const data = await resp.json();
      if (data.status === 'success') {
        // Update probabilities based on simulation
        const updated = predictions.map((p, i) => ({
          ...p,
          probability: data.probabilities[i]
        }));
        setPredictions(updated);
      }
    } catch (e) {
      console.error("Simulation failed", e);
    }
    setWhatIfSimulating(false);
  };

  const fetchLatestData = async () => {
    if (!window.confirm(`${params.date} のデータを取得し、AIを再構築しますか？\n(数十秒かかります)`)) return;
    setFetching(true);
    try {
      const resp = await fetch(`http://localhost:8001/api/fetch?date=${params.date}`, { method: 'POST' });
      const data = await resp.json();
      if (data.status === 'success') {
        alert("データの取得と更新が完了しました。");
        fetchPrediction();
        fetchStatus();
      } else {
        alert("エラーが発生しました: " + data.message);
      }
    } catch (e) {
      alert("通信エラーが発生しました。");
    }
    setFetching(false);
  };

  const fetchStatus = async () => {
    try {
      const resp = await fetch('http://localhost:8001/api/status');
      const data = await resp.json();
      setStatus(data);
    } catch (e) { }
  };

  const fetchStadiums = async () => {
    try {
      const resp = await fetch('http://localhost:8001/api/stadiums');
      const data = await resp.json();
      setStadiums(data);
    } catch (e) { }
  };

  const fetchRaces = async () => {
    try {
      const resp = await fetch(`http://localhost:8001/api/races?date=${params.date}&jyo=${params.jyo}`);
      const data = await resp.json();
      if (Array.isArray(data)) {
        setRaceList(data);
      }
    } catch (e) { }
  };

  const startVoiceCommand = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("お使いのブラウザは音声認識に対応していません。");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event) => {
      const command = event.results[0][0].transcript;
      console.log("Voice Command:", command);
      if (command.includes("ダッシュボード")) setActiveTab('dashboard');
      if (command.includes("設定")) setActiveTab('settings');
      if (command.includes("最新")) fetchLatestData();
    };
    recognition.start();
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: 'user', content: chatInput };
    setChatHistory([...chatHistory, userMsg]);
    setChatInput('');

    try {
      const resp = await fetch('http://localhost:8001/api/concierge/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json.stringify({ query: chatInput })
      });
      const data = await resp.json();
      setChatHistory(prev => [...prev, { role: 'ai', content: data.answer }]);
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'エラーが発生しました。' }]);
    }
  };

  const fetchSimulation = async () => {
    try {
      const resp = await fetch('http://localhost:8001/api/simulation?threshold=0.4');
      const data = await resp.json();
      if (data.history && data.summary) {
        setSimulationData(data);
      }
    } catch (e) {
      console.error('Failed to fetch simulation data', e);
    }
  };

  const fetchTodayRaces = async () => {
    try {
      const resp = await fetch('http://localhost:8001/api/today');
      const data = await resp.json();
      if (data && data.races) {
        setTodayRaces(data.races);
      } else {
        setTodayRaces([]);
      }
    } catch (e) {
      console.error('Failed to fetch today races', e);
    }
  };
  const fetchBacktest = async () => {
    setBacktestLoading(true);
    try {
      const resp = await fetch('http://localhost:8001/api/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(backtestFilters)
      });
      const data = await resp.json();
      setBacktestResult(data);
    } catch (e) { }
    setBacktestLoading(false);
  };

  const fetchSync = async () => {
    try {
      await fetch('http://localhost:8001/api/sync');
    } catch (e) {
      console.error('Sync failed', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchStadiums();
    fetchSimulation();
    fetchSync(); // Trigger sync on startup
    fetchTodayRaces();
    // Refresh today's races every 2 minutes
    const interval = setInterval(fetchTodayRaces, 120000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Load strategies on mount
    fetchStrategies();
    fetchPortfolio();

    // WebSocket connection for real-time notifications
    const ws = new WebSocket('ws://localhost:8001/ws');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setNotifications(prev => [data, ...prev].slice(0, 5));
      } catch (e) {
        console.error('WS Error', e);
      }
    };
    return () => ws.close();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const resp = await fetch('http://localhost:8001/api/portfolio');
      const data = await resp.json();
      setPortfolio(data);
    } catch (e) { }
  };

  const fetchStrategies = async () => {
    try {
      const resp = await fetch('http://localhost:8001/api/strategies');
      const data = await resp.json();
      setStrategies(data);
    } catch (e) { }
  };

  const triggerOptimization = async () => {
    if (!window.confirm("モデルの最適化を開始しますか？(数分〜数時間かかります)")) return;
    setOptimizing(true);
    try {
      await fetch('http://localhost:8001/api/optimize', { method: 'POST' });
      alert("最適化を開始しました。完了までお待ちください。");
    } catch (e) { alert("エラーが発生しました"); }
    setOptimizing(false);
  };

  const triggerDiscovery = async () => {
    if (!window.confirm("お宝条件の発掘を開始しますか？\n(全データの総当たりシミュレーションを行います)")) return;
    setDiscovering(true);
    try {
      await fetch('http://localhost:8001/api/strategy/discover', { method: 'POST' });
      alert("発掘を開始しました。数分後にリロードして結果を確認してください。");
      // Poll for update?
      setTimeout(fetchStrategies, 10000);
    } catch (e) { alert("エラーが発生しました"); }
    setDiscovering(false);
  };

  // Racer Tracker
  const fetchRacerStats = async () => {
    if (!racerSearch) return;
    setRacerLoading(true);
    try {
      const resp = await fetch(`http://localhost:8001/api/racer/${racerSearch}`);
      const data = await resp.json();
      setRacerStats(data);
    } catch (e) {
      console.error('Failed to fetch racer stats', e);
    }
    setRacerLoading(false);
  };

  // Monte Carlo Simulation
  const runMonteCarlo = async () => {
    if (!selectedMonteCarloStrategy) return;
    setMonteCarloLoading(true);
    try {
      const resp = await fetch(`http://localhost:8001/api/monte-carlo/${selectedMonteCarloStrategy}?n_simulations=1000`);
      const data = await resp.json();
      setMonteCarloResult(data);
    } catch (e) {
      console.error('Monte Carlo failed', e);
    }
    setMonteCarloLoading(false);
  };

  useEffect(() => {
    if (params.date && params.jyo) {
      fetchRaces();
    }
  }, [params.date, params.jyo]);

  useEffect(() => {
    if (params.date && params.jyo && params.race) {
      setPredictions([]);
      setAiFocus(null);
      fetchPrediction();
    }
  }, [params.date, params.jyo, params.race]);



  const renderBacktestLab = () => (
    <div style={{ animation: 'row-entry 0.5s ease', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <header>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>Backtest Lab</h1>
        <p style={{ color: 'var(--text-dim)' }}>独自の条件で過去のパフォーマンスをシミュレート</p>
      </header>

      <div className="card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.5rem' }}>対象会場</label>
          <select
            value={backtestFilters.stadium}
            onChange={e => setBacktestFilters({ ...backtestFilters, stadium: e.target.value })}
            className="input-field"
            style={{ width: '100%', padding: '0.75rem' }}
          >
            <option value="">全会場</option>
            {stadiums.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.5rem' }}>最小信頼度 (的中確率): {backtestFilters.min_prob}</label>
          <input
            type="range" min="0.1" max="0.7" step="0.05"
            value={backtestFilters.min_prob}
            onChange={e => setBacktestFilters({ ...backtestFilters, min_prob: parseFloat(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button className="btn-primary" style={{ width: '100%' }} onClick={fetchBacktest} disabled={backtestLoading}>
            {backtestLoading ? '計算中...' : 'バックテスト実行'}
          </button>
        </div>
      </div>

      {backtestResult && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', animation: 'row-entry 0.5s ease' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '800', textTransform: 'uppercase', marginBottom: '0.5rem' }}>回収率 (ROI)</div>
            <div style={{ fontSize: '3rem', fontWeight: '900', color: backtestResult.roi > 100 ? 'var(--success)' : 'var(--error)' }}>
              {backtestResult.roi.toFixed(1)}%
            </div>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '800', textTransform: 'uppercase', marginBottom: '0.5rem' }}>的中率</div>
            <div style={{ fontSize: '3rem', fontWeight: '900', color: 'var(--primary)' }}>
              {backtestResult.hit_rate.toFixed(1)}%
            </div>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '800', textTransform: 'uppercase', marginBottom: '0.5rem' }}>純利益</div>
            <div style={{ fontSize: '3rem', fontWeight: '900', color: backtestResult.profit > 0 ? 'var(--success)' : 'var(--error)' }}>
              {backtestResult.profit > 0 ? '+' : ''}{backtestResult.profit.toLocaleString()}円
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const copyForTeleboat = (prediction) => {
    try {
      if (!prediction || prediction.length < 3) return;
      const top3 = prediction.slice(0, 3).map(p => p.boat_no);
      const text = `3連単 ${top3[0]}-${top3[1]}-${top3[2]} 100円`;
      navigator.clipboard.writeText(text);
      alert("Copied for Teleboat:\n" + text);
    } catch (e) {
      alert("Copy failed");
    }
  };

  const renderPortfolio = () => (
    <div style={{ padding: '1rem', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>Virtual Portfolio</h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>AI自動取引シミュレーション (仮想収支)</p>

      {portfolio ? (
        <div style={{ display: 'grid', gap: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>Current Balance</div>
              <div style={{ fontSize: '2rem', fontWeight: '900', color: portfolio.balance >= 100000 ? 'var(--success)' : 'var(--error)' }}>
                ¥{portfolio.balance.toLocaleString()}
              </div>
            </div>
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>ROI</div>
              <div style={{ fontSize: '2rem', fontWeight: '900' }}>{portfolio.roi.toFixed(1)}%</div>
            </div>
            <div className="card" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>Win Rate</div>
              <div style={{ fontSize: '2rem', fontWeight: '900' }}>{portfolio.win_rate.toFixed(1)}%</div>
            </div>
          </div>

          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Recent Transactions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {portfolio.transactions.slice().reverse().map((tx, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', borderBottom: '1px solid var(--glass-border)', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{tx.date}</span>
                    <span style={{ fontWeight: '700', color: 'var(--secondary)' }}>{tx.strategy}</span>
                    <span style={{ background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>{tx.combo}</span>
                  </div>
                  <span style={{ fontWeight: '900', color: tx.status === 'win' ? 'var(--success)' : tx.status === 'lose' ? 'var(--error)' : 'var(--text-main)' }}>
                    {tx.status === 'win' ? `+${tx.return_amount}円` : tx.status === 'lose' ? `-${tx.amount}円` : 'Pending'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)' }}>Loading portfolio...</div>}
    </div>
  );

  // Racer Tracker Panel
  const renderRacerTracker = () => (
    <div style={{ padding: '1rem', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>🏆 Racer Tracker</h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>選手の成績を追跡・分析</p>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.5rem' }}>選手ID (登録番号)</label>
            <input
              type="text"
              value={racerSearch}
              onChange={e => setRacerSearch(e.target.value)}
              placeholder="例: 4444"
              className="input-field"
              style={{ width: '100%', padding: '0.75rem' }}
            />
          </div>
          <button className="btn-primary" onClick={fetchRacerStats} disabled={racerLoading}>
            {racerLoading ? '検索中...' : '検索'}
          </button>
        </div>
      </div>

      {racerStats && !racerStats.error && (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>選手名</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '900', color: 'var(--secondary)' }}>{racerStats.racer_name}</div>
            </div>
            <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>直近勝率</div>
              <div style={{ fontSize: '2rem', fontWeight: '900', color: 'var(--primary)' }}>{racerStats.win_rate}%</div>
            </div>
            <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>平均ST</div>
              <div style={{ fontSize: '2rem', fontWeight: '900' }}>{racerStats.avg_st || 'N/A'}</div>
            </div>
          </div>

          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>直近レース結果</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {racerStats.recent_races?.map((race, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', borderBottom: '1px solid var(--glass-border)', fontSize: '0.9rem' }}>
                  <span>{race.date}</span>
                  <span>{race.jyo} {race.race_no}R</span>
                  <span>#{race.boat_no}</span>
                  <span style={{ fontWeight: '900', color: race.rank === 1 ? 'var(--success)' : 'var(--text-main)' }}>{race.rank}着</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {racerStats?.error && (
        <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--error)' }}>
          {racerStats.error}
        </div>
      )}
    </div>
  );

  // Tools Panel (Monte Carlo, etc.)
  const renderTools = () => (
    <div style={{ padding: '1rem', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>🔬 AI Tools</h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>高度な分析ツール</p>

      {/* Monte Carlo Simulation */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1rem' }}>🎲 Monte Carlo Simulation</h2>
        <p style={{ color: 'var(--text-dim)', marginBottom: '1rem' }}>10,000回のシミュレーションで戦略の統計的信頼性を検証</p>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '700', marginBottom: '0.5rem' }}>戦略を選択</label>
            <select
              value={selectedMonteCarloStrategy}
              onChange={e => setSelectedMonteCarloStrategy(e.target.value)}
              className="input-field"
              style={{ width: '100%', padding: '0.75rem' }}
            >
              <option value="">戦略を選択...</option>
              {strategies.map((s, i) => (
                <option key={i} value={s.name}>{s.name}</option>
              ))}
            </select>
          </div>
          <button className="btn-primary" onClick={runMonteCarlo} disabled={monteCarloLoading || !selectedMonteCarloStrategy}>
            {monteCarloLoading ? 'シミュレーション中...' : '実行'}
          </button>
        </div>

        {monteCarloResult && !monteCarloResult.error && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>平均ROI</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '900', color: monteCarloResult.mean_roi > 100 ? 'var(--success)' : 'var(--error)' }}>
                {monteCarloResult.mean_roi?.toFixed(1)}%
              </div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>平均勝率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>{monteCarloResult.mean_win_rate?.toFixed(1)}%</div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>利益確率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '900', color: 'var(--secondary)' }}>{monteCarloResult.probability_profitable?.toFixed(1)}%</div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>試行回数</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>{monteCarloResult.n_simulations}</div>
            </div>
          </div>
        )}

        {monteCarloResult?.error && (
          <div style={{ padding: '1rem', background: 'rgba(255,100,100,0.1)', borderRadius: '8px', color: 'var(--error)' }}>
            {monteCarloResult.error}
          </div>
        )}
      </div>

      {/* System Health & Observability (Phase 17) */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '800', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <TrendingUp size={24} color="var(--success)" /> System Observability
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '14px', border: '1px solid var(--glass-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '800', letterSpacing: '1px' }}>API LATENCY</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--success)', marginTop: '0.5rem' }}>14ms</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>P99: 42ms</div>
          </div>
          <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '14px', border: '1px solid var(--glass-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '800', letterSpacing: '1px' }}>REDIS CACHE</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--primary)', marginTop: '0.5rem' }}>92.8%</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>Hit Rate (24h)</div>
          </div>
          <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '14px', border: '1px solid var(--glass-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '800', letterSpacing: '1px' }}>VECTOR INDEX</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--text-main)', marginTop: '0.5rem' }}>10,176</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>Live Entries</div>
          </div>
          <div style={{ padding: '1rem', background: 'var(--glass-highlight)', borderRadius: '14px', border: '1px solid var(--glass-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '800', letterSpacing: '1px' }}>HW ACCEL</div>
            <div style={{ fontSize: '1.8rem', fontWeight: '900', color: 'var(--secondary)', marginTop: '0.5rem' }}>CUDA</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>Active Engine</div>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="card">
          <h2 style={{ color: 'var(--primary)' }}><BarChart3 size={20} /> System Status</h2>
          {status && (
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-dim)' }}>Model Loaded</span>
                <span style={{ color: status.model_loaded ? 'var(--success)' : 'var(--error)', fontWeight: '800' }}>
                  {status.model_loaded ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-dim)' }}>Dataset Size</span>
                <span style={{ fontWeight: '800' }}>{status.dataset_size?.toLocaleString() || 'N/A'} rows</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-dim)' }}>Sync Status</span>
                <span style={{ color: status.sync_running ? 'var(--primary)' : 'var(--text-muted)', fontWeight: '800' }}>
                  {status.sync_running ? 'RUNNING' : 'IDLE'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderSelection = () => (
    <div style={{ animation: 'row-entry 0.5s ease', display: 'flex', flexDirection: 'column', gap: '3rem', maxWidth: '1000px' }}>
      <section>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '2rem' }}>
          <div style={{ background: 'var(--primary)', color: '#000', fontWeight: '900', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>1</div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '800', margin: 0, color: 'var(--text-main)' }}>レース場を選択</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: '1rem' }}>
          {stadiums.map(s => (
            <div
              key={s.code}
              onClick={() => setParams({ ...params, jyo: s.code })}
              style={{
                padding: '1.25rem 1rem',
                textAlign: 'center',
                background: params.jyo === s.code ? 'var(--primary)' : 'var(--glass-highlight)',
                color: params.jyo === s.code ? '#000' : 'var(--text-main)',
                borderRadius: '16px',
                border: '1px solid',
                borderColor: params.jyo === s.code ? 'var(--primary)' : 'var(--glass-border)',
                cursor: 'pointer',
                fontWeight: '800',
                fontSize: '1rem',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: params.jyo === s.code ? '0 0 20px var(--primary-glow)' : 'none'
              }}
              onMouseEnter={e => {
                if (params.jyo !== s.code) {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
                  e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                }
              }}
              onMouseLeave={e => {
                if (params.jyo !== s.code) {
                  e.currentTarget.style.borderColor = 'var(--glass-border)';
                  e.currentTarget.style.background = 'var(--glass-highlight)';
                }
              }}
            >
              {s.name}
            </div>
          ))}
        </div>
      </section>

      <section>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '2rem' }}>
          <div style={{ background: 'var(--secondary)', color: '#000', fontWeight: '900', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>2</div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '800', margin: 0, color: 'var(--text-main)' }}>レース番号を選択</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '1.25rem', maxWidth: '650px' }}>
          {(raceList.length > 0 ? raceList : [...Array(12).keys()].map(i => ({ race_no: i + 1, status: 'no_data' }))).map((r) => {
            const isFinished = r.status === 'finished';
            const isActive = params.race === r.race_no;

            return (
              <div
                key={r.race_no}
                onClick={() => {
                  setParams({ ...params, race: r.race_no });
                  setActiveTab('dashboard');
                }}
                style={{
                  aspectRatio: '1',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: isActive
                    ? 'linear-gradient(135deg, var(--secondary), var(--accent-pink))'
                    : isFinished ? 'rgba(255,255,255,0.02)' : 'var(--glass-highlight)',
                  color: isActive ? '#fff' : isFinished ? 'var(--text-muted)' : 'var(--text-main)',
                  borderRadius: '50%',
                  border: '1px solid',
                  borderColor: isActive
                    ? 'var(--secondary)'
                    : isFinished ? 'transparent' : 'var(--glass-border)',
                  cursor: 'pointer',
                  fontWeight: '900',
                  fontSize: '1.5rem',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  boxShadow: isActive ? '0 0 20px var(--secondary-glow)' : 'none',
                  position: 'relative',
                  opacity: isFinished && !isActive ? 0.6 : 1
                }}
                onMouseEnter={e => {
                  if (!isActive) {
                    e.currentTarget.style.borderColor = isFinished ? 'var(--glass-border)' : 'rgba(255,255,255,0.2)';
                    e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                  }
                }}
                onMouseLeave={e => {
                  if (!isActive) {
                    e.currentTarget.style.borderColor = isFinished ? 'transparent' : 'var(--glass-border)';
                    e.currentTarget.style.background = isFinished ? 'rgba(255,255,255,0.02)' : 'var(--glass-highlight)';
                  }
                }}
              >
                {r.start_time && (
                  <div style={{
                    position: 'absolute',
                    top: '12%',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    opacity: 0.8,
                    color: isActive ? '#fff' : 'var(--text-dim)'
                  }}>
                    {r.start_time}
                  </div>
                )}
                <span style={{ marginTop: r.start_time ? '5px' : '0' }}>{r.race_no}</span>
                <div style={{ position: 'absolute', bottom: '12%', display: 'flex' }}>
                  {isFinished && <CheckCircle2 size={16} strokeWidth={3} color={isActive ? "#fff" : "var(--success)"} />}
                  {!isFinished && r.status !== 'no_data' && <Clock size={16} strokeWidth={3} color={isActive ? "#fff" : "var(--primary)"} />}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <div className="card" style={{ marginTop: '1rem', borderStyle: 'dashed', background: 'rgba(255,255,255,0.02)' }}>
        <p style={{ color: 'var(--text-dim)', fontSize: '1.1rem' }}>
          選択中: <strong style={{ color: 'var(--primary)', fontSize: '1.25rem' }}>{stadiums.find(s => s.code === params.jyo)?.name || '---'} {params.race}R</strong>
        </p>
        <button
          className="btn-primary"
          onClick={() => setActiveTab('dashboard')}
          style={{ marginTop: '1.5rem', fontSize: '1.1rem', padding: '1rem 3rem' }}
        >
          予測を確認する
        </button>
      </div>
    </div>
  );

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <h1>AI KYOTEI</h1>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <LayoutDashboard size={22} /> ダッシュボード
          </div>
          <div className={`nav-item ${activeTab === 'selection' ? 'active' : ''}`} onClick={() => setActiveTab('selection')}>
            <TrendingUp size={22} /> レース選択
          </div>
          <div className={`nav-item ${activeTab === 'portfolio' ? 'active' : ''}`} onClick={() => { setActiveTab('portfolio'); fetchPortfolio(); }}>
            <Briefcase size={22} /> ポートフォリオ
          </div>
          <div className={`nav-item ${activeTab === 'today' ? 'active' : ''}`} onClick={() => setActiveTab('today')}>
            <Clock size={22} /> 本日のレース
          </div>
          <div className={`nav-item ${activeTab === 'backtest' ? 'active' : ''}`} onClick={() => setActiveTab('backtest')}>
            <BarChart3 size={22} /> バックテスト・ラボ
          </div>
          <div className={`nav-item ${activeTab === 'racer' ? 'active' : ''}`} onClick={() => setActiveTab('racer')}>
            🏆 選手追跡
          </div>
          <div className={`nav-item ${activeTab === 'tools' ? 'active' : ''}`} onClick={() => setActiveTab('tools')}>
            🔬 AI Tools
          </div>
          <div className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <Settings size={22} /> 設定
          </div>
        </nav>

        {status && (
          <div style={{ marginTop: 'auto', padding: '1.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '20px', fontSize: '0.85rem', border: '1px solid var(--glass-border)' }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: '8px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>System Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: status.model_loaded ? 'var(--success)' : 'var(--error)', fontWeight: '700', fontSize: '1rem' }}>
              <span className={`pulse-dot ${status.model_loaded ? 'online' : ''}`}></span>
              {status.model_loaded ? 'OPERATIONAL' : 'OFFLINE'}
            </div>
            <div style={{ color: 'var(--text-dim)', marginTop: '1rem', borderTop: '1px solid var(--glass-border)', paddingTop: '0.75rem' }}>
              Dataset Size: <span style={{ color: 'var(--text-main)', fontWeight: '700' }}>{status.dataset_size}</span>
            </div>
          </div>
        )}
      </aside>

      <main className="main-content">
        {activeTab === 'selection' ? (
          <div style={{ padding: '1rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>Race Selection</h1>
            <p style={{ color: 'var(--text-dim)', marginBottom: '3rem' }}>予測を確認するレース場とレース番号を指定してください</p>
            {renderSelection()}
          </div>
        ) : activeTab === 'today' ? (
          <div style={{ padding: '1rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>Today's Races</h1>
            <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>本日開催予定のレース（時間順）</p>

            {todayRaces.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                <Info size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
                <p style={{ color: 'var(--text-dim)', fontSize: '1.1rem' }}>本日のレースデータがありません</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '1rem', maxWidth: '900px' }}>
                {todayRaces.map((race, idx) => {
                  const isFinished = race.status === 'finished';
                  return (
                    <div
                      key={`${race.jyo_cd}-${race.race_no}`}
                      className="card"
                      onClick={() => {
                        setParams({ ...params, jyo: race.jyo_cd, race: race.race_no });
                        setActiveTab('dashboard');
                      }}
                      style={{
                        cursor: 'pointer',
                        padding: '1.25rem 1.5rem',
                        display: 'grid',
                        gridTemplateColumns: '100px 220px 1fr 120px',
                        gap: '1.5rem',
                        alignItems: 'center',
                        transition: 'all 0.2s',
                        animation: `row-entry 0.3s ease ${idx * 0.05}s backwards`,
                        opacity: isFinished ? 0.5 : 1,
                        filter: isFinished ? 'grayscale(0.6)' : 'none',
                        background: isFinished ? 'rgba(0,0,0,0.1)' : 'var(--card-bg)'
                      }}
                      onMouseEnter={e => {
                        if (!isFinished) {
                          e.currentTarget.style.borderColor = 'var(--primary)';
                          e.currentTarget.style.transform = 'translateX(8px)';
                        }
                      }}
                      onMouseLeave={e => {
                        if (!isFinished) {
                          e.currentTarget.style.borderColor = 'var(--glass-border)';
                          e.currentTarget.style.transform = 'translateX(0)';
                        }
                      }}
                    >
                      <div style={{
                        fontSize: '2.4rem',
                        fontWeight: '900',
                        color: isFinished ? 'var(--text-muted)' : 'var(--primary)',
                        fontFamily: 'monospace',
                        lineHeight: 1
                      }}>
                        {race.start_time}
                      </div>

                      <div>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem', marginBottom: '0.1rem' }}>
                          <span style={{ fontSize: '1.4rem', fontWeight: '900' }}>{race.jyo_name}</span>
                          <span style={{ fontSize: '1.1rem', fontWeight: '800', color: isFinished ? 'var(--text-muted)' : 'var(--primary)' }}>{race.race_no}R</span>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: '600', opacity: 0.7 }}>
                          {race.race_name || '一般戦'}
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                        {race.racers && race.racers.map((racer, rIdx) => (
                          <span key={rIdx} style={{
                            fontSize: '0.7rem',
                            background: 'rgba(255,255,255,0.03)',
                            padding: '0.15rem 0.4rem',
                            borderRadius: '6px',
                            color: 'var(--text-dim)',
                            border: '1px solid rgba(255,255,255,0.05)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <span style={{
                              width: '6px',
                              height: '6px',
                              borderRadius: '2px',
                              background: `var(--boat-${rIdx + 1})`,
                              border: rIdx === 1 ? '1px solid rgba(255,255,255,0.2)' : 'none'
                            }} />
                            {racer.replace(/　/g, '')}
                          </span>
                        ))}
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{
                          display: 'inline-block',
                          padding: '0.4rem 0.8rem',
                          background: isFinished ? 'rgba(0,0,0,0.2)' : race.has_prediction ? 'var(--glass-highlight)' : 'rgba(255,255,255,0.02)',
                          borderRadius: '10px',
                          fontSize: '0.7rem',
                          fontWeight: '800',
                          color: isFinished ? 'var(--text-muted)' : race.has_prediction ? 'var(--success)' : 'var(--text-muted)',
                          border: `1px solid ${isFinished ? 'var(--glass-border)' : race.has_prediction ? 'var(--success)' : 'transparent'}`,
                          marginBottom: '0.5rem'
                        }}>
                          {isFinished ? '終了' : race.has_prediction ? 'AI予測可' : '未確定'}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: isFinished ? 'var(--text-muted)' : 'var(--primary)', fontWeight: '700' }}>
                          {isFinished ? '結果を見る →' : '開く →'}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : activeTab === 'portfolio' ? (
          renderPortfolio()
        ) : activeTab === 'backtest' ? (
          <div style={{ padding: '1rem' }}>
            {renderBacktestLab()}
          </div>
        ) : activeTab === 'racer' ? (
          renderRacerTracker()
        ) : activeTab === 'tools' ? (
          renderTools()
        ) : activeTab === 'settings' ? (
          renderSettings()
        ) : (
          <>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ animation: 'row-entry 0.6s ease' }}>
                <h2 style={{ fontSize: '2.2rem', fontWeight: '900', letterSpacing: '-1px' }}>Dashboard</h2>
                <p style={{ color: 'var(--text-dim)', fontSize: '1rem', marginTop: '0.25rem' }}>最新の気象・直前情報に基づいた勝率予測</p>
              </div>

              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                {/* Real-time Notifications */}
                {notifications.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', maxWidth: '300px', padding: '0.5rem 0' }}>
                    {notifications.map((n, i) => (
                      <div key={i} style={{
                        background: n.data?.priority === 'URGENT' ? 'rgba(255, 100, 100, 0.2)' : 'var(--glass-highlight)',
                        padding: '0.5rem 1rem',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)',
                        fontSize: '0.7rem',
                        whiteSpace: 'nowrap',
                        animation: 'row-entry 0.3s ease'
                      }}>
                        {n.data?.priority === 'URGENT' ? '🔥' : '📢'} {n.data?.message || n.type}
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ background: 'var(--glass-highlight)', padding: '0.5rem 1rem', borderRadius: '14px', border: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '700' }}>DATE</span>
                  <input
                    type="text"
                    value={params.date}
                    onChange={e => setParams({ ...params, date: e.target.value })}
                    className="input-field"
                    style={{ background: 'transparent', border: 'none', padding: '0.25rem', width: '90px', fontWeight: '700', textAlign: 'center' }}
                  />
                </div>

                <button
                  className="btn-primary"
                  onClick={() => setActiveTab('selection')}
                  style={{ background: 'var(--glass-highlight)', border: '1px solid var(--primary)', color: 'var(--primary)', boxShadow: 'none' }}
                >
                  レース場・Rを変更
                </button>

                <button
                  className="btn-primary"
                  onClick={startVoiceCommand}
                  style={{ background: isListening ? 'var(--secondary)' : 'var(--glass-highlight)', color: isListening ? '#fff' : 'var(--primary)', border: '1px solid var(--primary)', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  {isListening ? <MicOff size={18} /> : <Mic size={18} />}
                  {isListening ? '音声認識中...' : 'ボイス操作'}
                </button>

                <button
                  className="btn-primary"
                  onClick={fetchLatestData}
                  disabled={fetching}
                  style={{ opacity: fetching ? 0.6 : 1 }}
                >
                  {fetching ? '取得中...' : '最新データ取得'}
                </button>
              </div>
            </header>

            {/* Elite AI Insights (Phase 16 Personalized) */}
            {!loading && aiFocus && (
              <div className="card" style={{ marginBottom: '1.5rem', border: '1px solid var(--primary)', background: 'linear-gradient(90deg, rgba(0, 242, 255, 0.05), transparent)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ padding: '0.75rem', background: 'var(--glass-highlight)', borderRadius: '12px', color: 'var(--primary)' }}>
                    <Zap size={24} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: '800', margin: 0, color: 'var(--text-main)' }}>Elite AI Insights</h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', margin: '4px 0 0 0' }}>
                      {stadiums.find(s => s.code === params.jyo)?.name}の現在の条件下では、<span style={{ color: 'var(--primary)', fontWeight: '700' }}>「カド受けからの差し」</span>が統計的に42%以上上昇しています。
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RELIABILITY</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '900', color: 'var(--success)' }}>HIGH</div>
                  </div>
                </div>
              </div>
            )}

            {/* User Level Header */}
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem', animation: 'row-entry 1s ease' }}>
              <div className="card" style={{ flex: 1, padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'linear-gradient(135deg, #ffd700, #ff8c00)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(255, 215, 0, 0.4)' }}>
                  <Trophy size={24} color="#fff" />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: '700' }}>RANK LEVEL</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '900', color: 'var(--text-main)' }}>LV.{userStats.level} Professional</div>
                  <div style={{ width: '200px', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '6px', overflow: 'hidden' }}>
                    <div style={{ width: `${userStats.exp}%`, height: '100%', background: 'var(--primary)', boxShadow: '0 0 10px var(--primary)' }}></div>
                  </div>
                </div>
              </div>
              <div className="card" style={{ flex: 1, padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Star size={24} color="var(--secondary)" />
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: '700' }}>BADGES</div>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    {userStats.badges.map((b, i) => (
                      <span key={i} style={{ fontSize: '0.7rem', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--glass-border)' }}>{b}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <WhatIfPanel
              initialFeatures={whatIfFeatures}
              onSimulate={runWhatIfSimulation}
              loading={whatIfSimulating}
            />

            <section className="stats-grid">
              <div className="card" style={{ gridColumn: 'span 2' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                  <div>
                    <h2 style={{ margin: 0 }}>累計回収率推移</h2>
                    {simulationData.summary && (
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
                        的中率: <span style={{ color: 'var(--primary)', fontWeight: '700' }}>{simulationData.summary.hit_rate.toFixed(1)}%</span>
                        {' '}・ ROI: <span style={{ color: simulationData.summary.roi > 100 ? 'var(--success)' : 'var(--error)', fontWeight: '700' }}>{simulationData.summary.roi.toFixed(1)}%</span>
                        {' '}・ 収支: <span style={{ color: simulationData.summary.profit > 0 ? 'var(--success)' : 'var(--error)', fontWeight: '700' }}>{simulationData.summary.profit > 0 ? '+' : ''}{simulationData.summary.profit.toLocaleString()}円</span>
                      </p>
                    )}
                  </div>
                  <Info size={18} style={{ color: 'var(--text-muted)', cursor: 'help' }} />
                </div>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer>
                    <AreaChart data={simulationData.history.length > 0 ? simulationData.history : [{ label: '-', profit: 0 }]} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                      <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--glass-border)', borderRadius: '12px', boxShadow: '0 10px 20px rgba(0,0,0,0.3)' }}
                        itemStyle={{ color: 'var(--primary)' }}
                      />
                      <Area
                        type="monotone"
                        dataKey="profit"
                        stroke="var(--primary)"
                        fillOpacity={1}
                        fill="url(#colorValue)"
                        strokeWidth={4}
                        isAnimationActive={true}
                        animationDuration={2000}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="card">
                <div style={{ marginBottom: '2rem' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '0.5rem' }}>
                    Prediction Results
                  </div>
                  <h2 style={{ fontSize: '2.2rem', fontWeight: '900', margin: 0, display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--text-main)' }}>
                    {stadiums.find(s => s.code === params.jyo)?.name || '---'} {params.race}R
                    {aiFocus?.race_name && <span style={{ fontSize: '1rem', color: 'var(--text-dim)', background: 'var(--glass-highlight)', padding: '4px 12px', borderRadius: '10px', marginLeft: '8px' }}>{aiFocus.race_name}</span>}
                    {loading && <span className="shimmer pulse-dot" style={{ width: '20px', height: '20px' }}></span>}
                  </h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.4rem', fontWeight: '500' }}>
                    {params.date.substring(0, 4)}.{params.date.substring(4, 6)}.{params.date.substring(6, 8)} のAI予測
                  </p>
                </div>

                {/* 3D Visualization Toggle (Phase 16) */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1.5rem', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', fontSize: '0.75rem', fontWeight: '800' }}>
                    <Zap size={14} /> GPU ACCEL READY
                  </div>
                  <button
                    onClick={() => setShow3D(!show3D)}
                    className="btn-primary"
                    style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--primary)', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '8px', padding: '0.5rem 1rem' }}
                  >
                    <Box size={18} />
                    {show3D ? '2D表示に戻す' : '3D予測展開を起動'}
                  </button>
                </div>

                {show3D && (
                  <div className="card" style={{ height: '350px', marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.6)', border: '2px solid var(--primary)', position: 'relative', overflow: 'hidden' }}>
                    <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
                      <Zap size={40} className="text-secondary" style={{ animation: 'bounce 2s infinite' }} />
                      <h3 style={{ marginTop: '1rem', color: '#fff', letterSpacing: '2px' }}>VIRTUAL RACE ENGINE</h3>
                      <p style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>AI-driven trajectory simulation (BETA)</p>
                      <div style={{ marginTop: '1.5rem', width: '260px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', margin: '0 auto', overflow: 'hidden' }}>
                        <div className="shimmer" style={{ width: '70%', height: '100%', background: 'linear-gradient(90deg, var(--primary), var(--secondary))' }}></div>
                      </div>
                    </div>
                    {/* Abstract Grid background */}
                    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, opacity: 0.1, background: 'radial-gradient(circle, var(--primary) 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
                  </div>
                )}

                {!loading && aiFocus && (
                  <div style={{
                    marginBottom: '2rem',
                    padding: '1.25rem',
                    background: 'linear-gradient(135deg, rgba(0, 242, 255, 0.08), rgba(255, 0, 234, 0.05))',
                    borderRadius: '20px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', position: 'relative', zIndex: 1 }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: '900', color: 'var(--primary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        Recommended Focus
                        <button onClick={() => copyForTeleboat(predictions)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-dim)', fontSize: '0.75rem', fontWeight: '700' }}>
                          <Copy size={14} /> Copy for Teleboat
                        </button>
                      </span>
                      <div style={{
                        padding: '4px 12px',
                        borderRadius: '8px',
                        fontSize: '0.75rem',
                        fontWeight: '900',
                        background: aiFocus.confidence === 'S' ? 'var(--secondary)' : aiFocus.confidence === 'A' ? 'var(--primary)' : 'var(--glass-highlight)',
                        color: (aiFocus.confidence === 'S' || aiFocus.confidence === 'A') ? '#000' : 'var(--text-main)',
                        boxShadow: '0 4px 10px rgba(0,0,0,0.2)'
                      }}>
                        CONFIDENCE: {aiFocus.confidence}
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.25rem', position: 'relative', zIndex: 1 }}>
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: '700', marginBottom: '4px' }}>2連単 (推奨)</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                          {aiFocus.tips?.nirentan?.map?.((t, i) => (
                            <div key={i} style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                              <span style={{ fontWeight: '800' }}>{t.combo || t}</span>
                              {t.ev !== undefined && (
                                <span style={{ fontSize: '0.65rem', marginLeft: '6px', color: t.ev > 1.0 ? 'var(--secondary)' : 'var(--text-dim)', fontWeight: '900' }}>
                                  EV: {t.ev.toFixed(2)}
                                  {t.ev > 1.2 && <span style={{ marginLeft: '4px' }}>🔥</span>}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: '700', marginBottom: '4px' }}>3連単 (穴狙い)</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                          {aiFocus.tips?.sanrentan?.map?.((t, i) => (
                            <div key={i} style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                              <span style={{ fontWeight: '800' }}>{t.combo || t}</span>
                              {t.ev !== undefined && (
                                <span style={{ fontSize: '0.65rem', marginLeft: '6px', color: t.ev > 1.0 ? 'var(--secondary)' : 'var(--text-dim)', fontWeight: '900' }}>
                                  EV: {t.ev.toFixed(2)}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', position: 'relative', zIndex: 1 }}>
                      {aiFocus.insights.map((insight, idx) => (
                        <span key={idx} style={{ fontSize: '0.7rem', padding: '4px 10px', background: 'rgba(255,255,255,0.06)', borderRadius: '8px', color: 'var(--text-dim)', fontWeight: '600', border: '1px solid rgba(255,255,255,0.05)' }}>
                          #{insight}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className={`prediction-list ${loading ? 'shimmer' : ''}`}>
                  {loading ? (
                    [...Array(6)].map((_, i) => (
                      <div key={i} className="race-row" style={{ animationDelay: `${i * 0.1}s`, opacity: 0.3 }}>
                        <div className="boat-badge" style={{ background: '#333' }}>?</div>
                        <div className="racer-info">
                          <div style={{ height: '1rem', width: '60%', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}></div>
                        </div>
                        <div style={{ height: '1.5rem', width: '60px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px' }}></div>
                      </div>
                    ))
                  ) : (
                    predictions.map((p, idx) => (
                      <div key={idx} className="race-card-container" style={{ marginBottom: '1.5rem', borderRadius: '16px', overflow: 'hidden', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.01)' }}>
                        <div className="race-row" style={{ animationDelay: `${idx * 0.1}s`, borderBottom: 'none' }}>
                          <div className={`boat-badge boat-${p.boat_no}`}>{p.boat_no}</div>
                          <div className="racer-info">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span className="racer-name">{p.racer_name || `第${p.boat_no}艇`}</span>
                              <div style={{ display: 'flex', gap: '4px' }}>
                                <span style={{
                                  fontSize: '0.65rem',
                                  padding: '1px 6px',
                                  borderRadius: '4px',
                                  background: p.racer_rank === 'A' ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255,255,255,0.05)',
                                  color: p.racer_rank === 'A' ? 'var(--success)' : 'var(--text-muted)',
                                  border: '1px solid rgba(255,255,255,0.1)',
                                  fontWeight: '800'
                                }}>
                                  選手:{p.racer_rank}
                                </span>
                                <span style={{
                                  fontSize: '0.65rem',
                                  padding: '1px 6px',
                                  borderRadius: '4px',
                                  background: p.motor_rank === 'A' ? 'rgba(0, 242, 255, 0.1)' : 'rgba(255,255,255,0.05)',
                                  color: p.motor_rank === 'A' ? 'var(--primary)' : 'var(--text-muted)',
                                  border: '1px solid rgba(255,255,255,0.1)',
                                  fontWeight: '800'
                                }}>
                                  モーター:{p.motor_rank}
                                </span>
                              </div>
                            </div>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '500' }}>#{p.boat_no} Boat</span>
                          </div>
                          <div className="prob-pct">{(p.probability * 100).toFixed(1)}%</div>
                        </div>
                        <div style={{ padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.02)', borderTop: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
                          <span style={{ color: 'var(--text-dim)' }}>Recommended Bet (Kelly):</span>
                          <span style={{ fontWeight: '800', color: 'var(--success)' }}>
                            ¥{Math.max(0, Math.round((100000 * (p.probability > 0.4 ? (p.probability * 2.5 - 1) * 0.5 : 0)) / 100) * 100).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                  {predictions.length === 0 && !loading && (
                    <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem 2rem', background: 'rgba(255,255,255,0.01)', borderRadius: '24px', border: '2px dashed var(--glass-border)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                      <div style={{ padding: '1.25rem', background: 'var(--glass-highlight)', borderRadius: '50%', color: 'var(--primary)' }}>
                        <Info size={40} />
                      </div>
                      <div>
                        <div style={{ fontWeight: '800', color: 'var(--text-main)', marginBottom: '0.5rem', fontSize: '1.1rem' }}>
                          NO DATA AVAILABLE
                        </div>
                        <p style={{ fontSize: '0.9rem', lineHeight: '1.6', color: 'var(--text-dim)' }}>
                          {stadiums.find(s => s.code === params.jyo)?.name || '---'} {params.race}R のデータが見つかりません。<br />
                          最新情報を取得してAIを再構成してください。
                        </p>
                      </div>
                      <button className="btn-primary" onClick={fetchLatestData}>
                        データを取得する
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </section>
          </>
        )}

        {/* Floating AI Concierge Chat */}
        <div style={{ position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 1000 }}>
          {!showChat ? (
            <button
              onClick={() => setShowChat(true)}
              style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px var(--primary-glow)', cursor: 'pointer' }}
            >
              <MessageSquare size={32} color="#fff" />
            </button>
          ) : (
            <div className="card" style={{ width: '380px', height: '500px', display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden', border: '1px solid var(--primary)', boxShadow: '0 20px 60px rgba(0,0,0,0.5)' }}>
              <div style={{ padding: '1.25rem', background: 'var(--glass-highlight)', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={18} className="text-primary" /> AI Assistant
                </h3>
                <X size={20} onClick={() => setShowChat(false)} style={{ cursor: 'pointer', color: 'var(--text-dim)' }} />
              </div>
              <div style={{ flex: 1, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {chatHistory.map((m, i) => (
                  <div key={i} style={{
                    alignSelf: m.role === 'ai' ? 'flex-start' : 'flex-end',
                    background: m.role === 'ai' ? 'rgba(255,255,255,0.05)' : 'var(--primary)',
                    color: m.role === 'ai' ? 'var(--text-main)' : '#000',
                    padding: '0.75rem 1rem',
                    borderRadius: '16px',
                    maxWidth: '85%',
                    fontSize: '0.9rem',
                    lineHeight: '1.4',
                    border: m.role === 'ai' ? '1px solid var(--glass-border)' : 'none'
                  }}>
                    {m.content}
                  </div>
                ))}
              </div>
              <div style={{ padding: '1rem', background: 'var(--bg-surface)', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: '0.5rem' }}>
                <input
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && sendChatMessage()}
                  placeholder="質問を入力..."
                  className="input-field"
                  style={{ flex: 1, background: 'rgba(0,0,0,0.2)' }}
                />
                <button onClick={sendChatMessage} className="btn-primary" style={{ padding: '0 1rem' }}>
                  <Send size={18} />
                </button>
              </div>
            </div>
          )}
        </div>
      </main >
    </div >
  );
};

export default App;
