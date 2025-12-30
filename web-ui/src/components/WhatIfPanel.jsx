import React, { useState, useEffect } from 'react';
import { Sliders, RotateCcw, Zap } from 'lucide-react';

const WhatIfPanel = ({ initialFeatures, onSimulate, loading }) => {
    const [features, setFeatures] = useState(initialFeatures || {});

    // Sync if initialFeatures changes
    useEffect(() => {
        if (initialFeatures) {
            setFeatures(initialFeatures);
        }
    }, [initialFeatures]);

    const handleChange = (key, value) => {
        setFeatures(prev => ({ ...prev, [key]: parseFloat(value) }));
    };

    const handleReset = () => {
        setFeatures(initialFeatures);
    };

    return (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sliders size={20} className="text-primary" />
                    Interactive SHAP (What-if分析)
                </h3>
                <button onClick={handleReset} className="btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
                    <RotateCcw size={14} style={{ marginRight: '4px' }} /> リセット
                </button>
            </div>

            <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                レース条件を調整して、AI予測がどう変化するかシミュレーションします。
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                {/* Wind Speed */}
                <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                        風速 (m): {features.wind_speed?.toFixed(1) || '0.0'}
                    </label>
                    <input
                        type="range" min="0" max="15" step="0.5"
                        value={features.wind_speed || 0}
                        onChange={(e) => handleChange('wind_speed', e.target.value)}
                        style={{ width: '100%' }}
                    />
                </div>

                {/* Wave Height */}
                <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                        波高 (cm): {features.wave_height?.toFixed(0) || '0'}
                    </label>
                    <input
                        type="range" min="0" max="10" step="1"
                        value={features.wave_height || 0}
                        onChange={(e) => handleChange('wave_height', e.target.value)}
                        style={{ width: '100%' }}
                    />
                </div>

                {/* Temperature */}
                <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                        気温 (℃): {features.temperature?.toFixed(0) || '20'}
                    </label>
                    <input
                        type="range" min="0" max="40" step="1"
                        value={features.temperature || 20}
                        onChange={(e) => handleChange('temperature', e.target.value)}
                        style={{ width: '100%' }}
                    />
                </div>

                {/* Water Temp */}
                <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                        水温 (℃): {features.water_temp?.toFixed(0) || '20'}
                    </label>
                    <input
                        type="range" min="0" max="40" step="1"
                        value={features.water_temp || 20}
                        onChange={(e) => handleChange('water_temp', e.target.value)}
                        style={{ width: '100%' }}
                    />
                </div>
            </div>

            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                    className="btn-primary"
                    onClick={() => onSimulate(features)}
                    disabled={loading}
                    style={{ width: '200px' }}
                >
                    {loading ? '計算中...' : (
                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                            <Zap size={18} /> シミュレーション実行
                        </span>
                    )}
                </button>
            </div>
        </div>
    );
};

export default WhatIfPanel;
