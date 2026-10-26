import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Brush,
} from 'recharts';

function CustomTooltip({ active, payload, label, onSelectInterval }) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  const actual = data.actualMw;
  const forecast = data.forecastMw;
  const error = data.signedErrorMw;
  const pubTime = data.publishTimeLocal;
  const leadHours = data.leadTimeHours;

  return (
    <div className="custom-tooltip">
      <div className="tooltip-time">Delivery: {data.startTimeLocal} GMT</div>
      <div className="tooltip-row">
        <span className="tooltip-label" style={{ color: '#06b6d4' }}>● Actual Generation:</span>
        <span className="tooltip-val num-tabular">
          {actual !== null && actual !== undefined ? `${actual.toLocaleString()} MW` : 'N/A'}
        </span>
      </div>
      <div className="tooltip-row">
        <span className="tooltip-label" style={{ color: '#818cf8' }}>● Selected Forecast:</span>
        <span className="tooltip-val num-tabular">
          {forecast !== null && forecast !== undefined ? `${forecast.toLocaleString()} MW` : 'No Eligible FC'}
        </span>
      </div>
      {error !== null && error !== undefined && (
        <div className="tooltip-row">
          <span className="tooltip-label">Error (F - A):</span>
          <span
            className="tooltip-val num-tabular"
            style={{ color: error > 0 ? '#fb7185' : '#fbbf24' }}
          >
            {error > 0 ? `+${error.toLocaleString()}` : error.toLocaleString()} MW
          </span>
        </div>
      )}
      {pubTime && (
        <div className="tooltip-row" style={{ fontSize: '0.72rem', marginTop: '0.35rem' }}>
          <span className="tooltip-label">Published:</span>
          <span>{pubTime} ({leadHours}h lead)</span>
        </div>
      )}
      <div style={{ marginTop: '0.5rem', fontSize: '0.72rem', color: '#38bdf8', textAlign: 'center' }}>
        Click point to view publication history
      </div>
    </div>
  );
}

export default function TimeSeriesChart({ records, onSelectInterval }) {
  if (!records || records.length === 0) {
    return (
      <div className="glass-card chart-card">
        <div className="state-container">
          <p>No forecast records available for the selected filters.</p>
        </div>
      </div>
    );
  }

  // Format records for chart (sample down slightly if needed or display with brush)
  const chartData = records.map((r) => ({
    ...r,
    formattedTime: r.startTimeLocal.substring(5), // "MM-DD HH:mm"
  }));

  return (
    <div className="glass-card chart-card" id="time-series-chart-card">
      <div className="chart-header">
        <div className="chart-title-group">
          <h2>Actual vs Eligible Forecast Generation</h2>
          <p className="chart-subtitle">
            National wind outturn (FUELHH) versus day-ahead snapshot forecast (WINDFOR) in Megawatts (MW)
          </p>
        </div>

        <div className="chart-legend-custom">
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: '#06b6d4' }} />
            <span>Actual Outturn (MW)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: '#818cf8' }} />
            <span>Selected Forecast (MW)</span>
          </div>
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
            onClick={(e) => {
              if (e && e.activePayload && e.activePayload.length) {
                const item = e.activePayload[0].payload;
                if (onSelectInterval) onSelectInterval(item.startTimeUtc);
              }
            }}
          >
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#818cf8" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0.0} />
              </linearGradient>
            </defs>

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
              tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
              domain={[0, 'auto']}
            />
            <Tooltip content={<CustomTooltip onSelectInterval={onSelectInterval} />} />

            <Area
              type="monotone"
              dataKey="actualMw"
              name="Actual Outturn"
              stroke="#06b6d4"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorActual)"
              isAnimationActive={false}
            />

            <Line
              type="monotone"
              dataKey="forecastMw"
              name="Selected Forecast"
              stroke="#818cf8"
              strokeWidth={2}
              strokeDasharray="4 2"
              dot={false}
              activeDot={{ r: 6, fill: '#818cf8', stroke: '#ffffff' }}
              connectNulls={true}
              isAnimationActive={false}
            />

            <Brush
              dataKey="formattedTime"
              height={26}
              stroke="#0284c7"
              fill="rgba(15, 23, 42, 0.9)"
              tickFormatter={() => ''}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
