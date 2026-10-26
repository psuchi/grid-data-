import React, { useEffect, useState } from 'react';
import { X, Clock, CheckCircle2, AlertCircle, History, Zap } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { fetchForecastHistory } from '../services/api';

export default function ForecastHistoryModal({ deliveryTime, cutoffType, onClose }) {
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!deliveryTime) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    fetchForecastHistory(deliveryTime, cutoffType)
      .then((data) => {
        if (mounted) {
          setHistoryData(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [deliveryTime, cutoffType]);

  if (!deliveryTime) return null;

  return (
    <div className="modal-overlay" onClick={onClose} id="history-modal-overlay">
      <div className="modal-content" onClick={(e) => e.stopPropagation()} id="history-modal-content">
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <History size={20} style={{ color: '#0ea5e9' }} />
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                Forecast Publication Evolution History
              </h3>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                Tracking forecast adjustments across successive Elexon WINDFOR runs leading to delivery
              </p>
            </div>
          </div>
          <button className="close-btn" onClick={onClose} title="Close Modal" id="btn-close-modal">
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="state-container">
              <div className="spinner" />
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Loading publication history...</p>
            </div>
          )}

          {error && (
            <div className="state-container" style={{ color: '#fb7185' }}>
              <AlertCircle size={28} style={{ marginBottom: '0.5rem' }} />
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && historyData && (
            <>
              {/* Summary Header Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Delivery Interval</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginTop: 2 }}>{historyData.deliveryTimeLocal} GMT</div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{historyData.deliveryTimeUtc}</div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Actual Outturn</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#06b6d4', marginTop: 2 }} className="num-tabular">
                    {historyData.actualMw !== null ? `${historyData.actualMw.toLocaleString()} MW` : 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>FUELHH National Wind</div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Selected Eligible Forecast</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#818cf8', marginTop: 2 }} className="num-tabular">
                    {historyData.selectedForecast ? `${historyData.selectedForecast.forecastMw.toLocaleString()} MW` : 'None before cutoff'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                    {historyData.selectedForecast ? `Published: ${historyData.selectedForecast.publishTimeLocal}` : 'No eligible submission'}
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Decision Cutoff</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', marginTop: 2 }}>{historyData.cutoffDescription}</div>
                  <div style={{ fontSize: '0.7rem', color: '#fbbf24' }}>Cutoff: {historyData.cutoffTimeUtc?.substring(0, 16).replace('T', ' ')} UTC</div>
                </div>
              </div>

              {/* Forecast Evolution Timeline Chart */}
              {historyData.records.length > 0 ? (
                <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '1rem', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.5rem' }}>
                    Forecast Trajectory vs Actual Outturn (by Publication Lead Time)
                  </div>
                  <div style={{ width: '100%', height: 220 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={historyData.records}
                        margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.06)" />
                        <XAxis
                          dataKey="publishTimeLocal"
                          stroke="#64748b"
                          tick={{ fill: '#94a3b8', fontSize: 10 }}
                          tickFormatter={(v) => v.substring(5)}
                        />
                        <YAxis
                          stroke="#64748b"
                          tick={{ fill: '#94a3b8', fontSize: 10 }}
                          unit=" MW"
                          domain={['auto', 'auto']}
                        />
                        {historyData.actualMw !== null && (
                          <ReferenceLine
                            y={historyData.actualMw}
                            stroke="#06b6d4"
                            strokeWidth={2}
                            strokeDasharray="4 4"
                            label={{ value: 'Actual Outturn', fill: '#06b6d4', fontSize: 11, position: 'insideBottomRight' }}
                          />
                        )}
                        <Tooltip
                          content={({ active, payload }) => {
                            if (!active || !payload || !payload.length) return null;
                            const d = payload[0].payload;
                            return (
                              <div className="custom-tooltip">
                                <div className="tooltip-time">Published: {d.publishTimeLocal}</div>
                                <div className="tooltip-row">
                                  <span className="tooltip-label">Forecast:</span>
                                  <span className="tooltip-val num-tabular">{d.forecastMw.toLocaleString()} MW</span>
                                </div>
                                <div className="tooltip-row">
                                  <span className="tooltip-label">Lead Time:</span>
                                  <span className="tooltip-val num-tabular">{d.leadTimeHours} hrs</span>
                                </div>
                                <div className="tooltip-row">
                                  <span className="tooltip-label">Status:</span>
                                  <span style={{ color: d.isBeforeCutoff ? '#10b981' : '#fb7185', fontWeight: 600 }}>
                                    {d.isBeforeCutoff ? 'Eligible (Before Cutoff)' : 'Post-Cutoff'}
                                  </span>
                                </div>
                                {d.errorMw !== null && (
                                  <div className="tooltip-row">
                                    <span className="tooltip-label">Error vs Actual:</span>
                                    <span className="tooltip-val num-tabular">
                                      {d.errorMw > 0 ? `+${d.errorMw.toLocaleString()}` : d.errorMw.toLocaleString()} MW
                                    </span>
                                  </div>
                                )}
                              </div>
                            );
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="forecastMw"
                          stroke="#818cf8"
                          strokeWidth={2}
                          dot={{ r: 4, fill: '#818cf8' }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8' }}>
                  No historical forecast submissions found for this delivery timestamp in the WINDFOR feed.
                </div>
              )}

              {/* Submissions Detail Table */}
              <div style={{ maxHeight: 220, overflowY: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Publish Time (GMT)</th>
                      <th>Lead Time</th>
                      <th>Forecast (MW)</th>
                      <th>Error (MW)</th>
                      <th>Cutoff Status</th>
                      <th>Selection</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyData.records.map((r, i) => {
                      const isSelected = historyData.selectedForecast?.publishTimeUtc === r.publishTimeUtc;
                      return (
                        <tr
                          key={i}
                          style={{
                            backgroundColor: isSelected ? 'rgba(14, 165, 233, 0.15)' : 'transparent',
                          }}
                        >
                          <td className="highlight">{r.publishTimeLocal}</td>
                          <td className="num-tabular">{r.leadTimeHours} hrs</td>
                          <td className="num-tabular" style={{ color: '#818cf8', fontWeight: 600 }}>
                            {r.forecastMw.toLocaleString()} MW
                          </td>
                          <td className="num-tabular">
                            {r.errorMw !== null ? (
                              <span style={{ color: r.errorMw > 0 ? '#fb7185' : '#fbbf24' }}>
                                {r.errorMw > 0 ? `+${r.errorMw.toLocaleString()}` : r.errorMw.toLocaleString()}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td>
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4,
                                padding: '2px 8px',
                                borderRadius: 9999,
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                backgroundColor: r.isBeforeCutoff ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                                color: r.isBeforeCutoff ? '#34d399' : '#fb7185',
                              }}
                            >
                              {r.isBeforeCutoff ? 'Eligible' : 'Post-Cutoff'}
                            </span>
                          </td>
                          <td>
                            {isSelected ? (
                              <span style={{ color: '#38bdf8', fontWeight: 700, fontSize: '0.75rem' }}>
                                ★ Selected
                              </span>
                            ) : (
                              <span style={{ color: '#64748b', fontSize: '0.75rem' }}>—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
