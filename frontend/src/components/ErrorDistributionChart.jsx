import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from 'recharts';

function ErrorTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  const error = data.signedErrorMw;
  const actual = data.actualMw;
  const forecast = data.forecastMw;

  return (
    <div className="custom-tooltip">
      <div className="tooltip-time">Delivery: {data.startTimeLocal} GMT</div>
      <div className="tooltip-row">
        <span className="tooltip-label">Error (F - A):</span>
        <span
          className="tooltip-val num-tabular"
          style={{ color: error > 0 ? '#fb7185' : '#fbbf24', fontSize: '0.95rem' }}
        >
          {error > 0 ? `+${error.toLocaleString()}` : error.toLocaleString()} MW
        </span>
      </div>
      <div className="tooltip-row" style={{ fontSize: '0.72rem' }}>
        <span className="tooltip-label">Condition:</span>
        <span style={{ fontWeight: 600 }}>
          {error > 0 ? 'Overforecast (Surplus Risk)' : 'Underforecast (Deficit Risk)'}
        </span>
      </div>
      <div className="tooltip-row" style={{ fontSize: '0.72rem' }}>
        <span className="tooltip-label">Actual:</span>
        <span className="num-tabular">{actual?.toLocaleString() || 'N/A'} MW</span>
      </div>
      <div className="tooltip-row" style={{ fontSize: '0.72rem' }}>
        <span className="tooltip-label">Forecast:</span>
        <span className="num-tabular">{forecast?.toLocaleString() || 'N/A'} MW</span>
      </div>
    </div>
  );
}

export default function ErrorDistributionChart({ records, onSelectInterval }) {
  // Filter to records that have a signed error
  const validRecords = (records || [])
    .filter((r) => r.signedErrorMw !== null && r.signedErrorMw !== undefined)
    .map((r) => ({
      ...r,
      formattedTime: r.startTimeLocal.substring(5),
    }));

  if (validRecords.length === 0) {
    return null;
  }

  return (
    <div className="glass-card chart-card" id="error-distribution-chart-card">
      <div className="chart-header">
        <div className="chart-title-group">
          <h2>Forecast Error Divergence (F - A)</h2>
          <p className="chart-subtitle">
            Signed error profile across delivery intervals in Megawatts (MW). Positive = Overforecast, Negative = Underforecast.
          </p>
        </div>

        <div className="chart-legend-custom">
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: '#f43f5e' }} />
            <span>Overforecast (Surplus)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: '#f59e0b' }} />
            <span>Underforecast (Deficit)</span>
          </div>
        </div>
      </div>

      <div className="chart-wrapper" style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={validRecords}
            margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
            onClick={(e) => {
              if (e && e.activePayload && e.activePayload.length) {
                const item = e.activePayload[0].payload;
                if (onSelectInterval) onSelectInterval(item.startTimeUtc);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.06)" />
            <XAxis
              dataKey="formattedTime"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              minTickGap={40}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              unit=" MW"
              tickFormatter={(v) => (Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
            />
            <ReferenceLine y={0} stroke="rgba(255, 255, 255, 0.25)" strokeWidth={1} />
            <Tooltip content={<ErrorTooltip />} />

            <Bar dataKey="signedErrorMw" name="Forecast Error" isAnimationActive={false}>
              {validRecords.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.signedErrorMw > 0 ? '#f43f5e' : '#f59e0b'}
                  opacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
