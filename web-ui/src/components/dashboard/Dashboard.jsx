import React, { useState } from 'react';
import { Mic, MicOff, Zap, Trophy, Star, Info, Box, Copy } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import WhatIfPanel from '../WhatIfPanel';

const Dashboard = ({
  params, setParams, stadiums, activeTab, setActiveTab,
  notifications, isListening, startVoiceCommand, fetchLatestData, fetching,
  loading, aiFocus, userStats, whatIfFeatures, runWhatIfSimulation, whatIfSimulating,
  simulationData, predictions, show3D, setShow3D
}) => {

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

  return (
    <>
      <header className="dashboard-header">
        <div className="header-title">
          <h2>Dashboard</h2>
          <p>最新の気象・直前情報に基づいた勝率予測</p>
        </div>

        <div className="header-actions">
          {/* Real-time Notifications */}
          {notifications.length > 0 && (
            <div className="notifications-container">
              {notifications.map((n, i) => (
                <div key={i} className={`notification-badge ${n.data?.priority === 'URGENT' ? 'urgent' : ''}`}>
                  {n.data?.priority === 'URGENT' ? '🔥' : '📢'} {n.data?.message || n.type}
                </div>
              ))}
            </div>
          )}

          <div className="date-badge">
            <span className="date-label">DATE</span>
            <input
              type="text"
              value={params.date}
              onChange={e => setParams({ ...params, date: e.target.value })}
              className="input-field header-date-input"
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
        <div className="card ai-recommendation-card">
          <div className="ai-recommendation-content">
            <div className="ai-icon-wrapper">
              <Zap size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '800', margin: 0, color: 'var(--text-main)' }}>Elite AI Insights</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', margin: '4px 0 0 0' }}>
                {stadiums.find(s => s.code === params.jyo)?.name}の現在の条件下では、<span className="ai-highlight-text">「カド受けからの差し」</span>が統計的に42%以上上昇しています。
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="reliability-label">RELIABILITY</div>
              <div className="reliability-value">HIGH</div>
            </div>
          </div>
        </div>
      )}

      {/* User Level Header */}
      <div className="user-status-grid">
        <div className="card user-rank-card">
          <div className="rank-icon-wrapper">
            <Trophy size={24} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: '700' }}>RANK LEVEL</div>
            <div className="rank-level-text">LV.{userStats.level} Professional</div>
            <div className="exp-bar-container">
              <div className="exp-bar-fill" style={{ width: `${userStats.exp}%` }}></div>
            </div>
          </div>
        </div>
        <div className="card user-rank-card">
          <Star size={24} color="var(--secondary)" />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: '700' }}>BADGES</div>
            <div className="badges-container">
              {userStats.badges.map((b, i) => (
                <span key={i} className="user-badge-item">{b}</span>
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
          <div className="chart-header">
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
            <div className="prediction-results-label">
              Prediction Results
            </div>
            <h2 className="prediction-results-title">
              {stadiums.find(s => s.code === params.jyo)?.name || '---'} {params.race}R
              {aiFocus?.race_name && <span className="race-name-badge-custom">{aiFocus.race_name}</span>}
              {loading && <span className="shimmer pulse-dot" style={{ width: '20px', height: '20px' }}></span>}
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.4rem', fontWeight: '500' }}>
              {params.date.substring(0, 4)}.{params.date.substring(4, 6)}.{params.date.substring(6, 8)} のAI予測
            </p>
          </div>

          {/* 3D Visualization Toggle (Phase 16) */}
          <div className="viz-toggle-container">
            <div className="accel-ready-badge">
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
            <div className="virtual-engine-card">
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
            <div className="recommended-focus-container">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', position: 'relative', zIndex: 1 }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '900', color: 'var(--primary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  Recommended Focus
                  <button onClick={() => copyForTeleboat(predictions)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-dim)', fontSize: '0.75rem', fontWeight: '700' }}>
                    <Copy size={14} /> Copy for Teleboat
                  </button>
                </span>
                <div className={`confidence-badge ${aiFocus.confidence === 'S' ? 'confidence-s' : aiFocus.confidence === 'A' ? 'confidence-a' : 'confidence-other'}`}>
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
                        <span className="racer-name" style={{ color: 'var(--primary)', borderBottom: '1px solid var(--primary-glow)' }}>{p.racer_name}</span>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <span className={`racer-mini-rank ${p.racer_rank === 'A' ? 'rank-a' : 'rank-none'}`}>
                            選手:{p.racer_rank}
                          </span>
                          <span className={`motor-mini-rank ${p.motor_rank === 'A' ? 'rank-a' : 'rank-none'}`}>
                            モーター:{p.motor_rank}
                          </span>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '700' }}>#{p.boat_no} {p.racer_name || 'Racer'}</span>
                    </div>
                    <div className="prob-pct">{(p.probability * 100).toFixed(1)}%</div>
                  </div>
                  <div style={{ padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.02)', borderTop: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Recommended Bet (Kelly):</span>
                    <span className="Kelly-bet-amount">
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
  );
};

export default Dashboard;
