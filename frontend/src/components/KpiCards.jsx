import React from 'react';
import { Target, TrendingUp, Compass, Layers, Percent } from 'lucide-react';

export default function KpiCards({ accuracy }) {
  if (!accuracy) return null;

  const {
    mae,
    rmse,
    bias,
    mape,
    matched_sample_count,
    total_delivery_periods,
    coverage_percentage,
    overforecast_count,
    underforecast_count,
    zero_actual_count,
    mean_actual,
    mean_forecast,
  } = accuracy;

  const isOverforecast = (bias ?? 0) > 0;
  const biasLabel = isOverforecast ? 'Overforecast (+)' : 'Underforecast (-)';
  const biasTagClass = isOverforecast ? 'bias-tag over' : 'bias-tag under';

  return (
    <div className="kpi-grid" id="kpi-cards-grid">
      {/* MAE Card */}
      <div className="glass-card kpi-card mae" id="kpi-card-mae">
        <div className="kpi-top">
          <span className="kpi-title">Mean Absolute Error (MAE)</span>
          <div className="kpi-icon-badge">
            <Target size={16} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value num-tabular">
            {mae !== null && mae !== undefined ? mae.toLocaleString() : '—'}
          </span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-footer">
          <span>Magnitude of average divergence</span>
          <span className="num-tabular">
            {mean_actual && mae ? `${((mae / mean_actual) * 100).toFixed(1)}% of mean` : ''}
          </span>
        </div>
      </div>

      {/* RMSE Card */}
      <div className="glass-card kpi-card rmse" id="kpi-card-rmse">
        <div className="kpi-top">
          <span className="kpi-title">Root Mean Squared Error (RMSE)</span>
          <div className="kpi-icon-badge">
            <TrendingUp size={16} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value num-tabular">
            {rmse !== null && rmse !== undefined ? rmse.toLocaleString() : '—'}
          </span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-footer">
          <span>Penalizes larger forecast spikes</span>
          <span className="num-tabular">
            {mae && rmse ? `Ratio: ${(rmse / mae).toFixed(2)}` : ''}
          </span>
        </div>
      </div>

      {/* Bias Card */}
      <div className={`glass-card kpi-card ${isOverforecast ? 'bias-over' : 'bias-under'}`} id="kpi-card-bias">
        <div className="kpi-top">
          <span className="kpi-title">Mean Signed Error (Bias)</span>
          <div className="kpi-icon-badge">
            <Compass size={16} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value num-tabular">
            {bias !== null && bias !== undefined ? (bias > 0 ? `+${bias.toLocaleString()}` : bias.toLocaleString()) : '—'}
          </span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-footer">
          <span className={biasTagClass}>{biasLabel}</span>
          <span className="num-tabular" style={{ fontSize: '0.72rem' }}>
            {overforecast_count} over / {underforecast_count} under
          </span>
        </div>
      </div>

      {/* Matched Periods Card */}
      <div className="glass-card kpi-card matched" id="kpi-card-matched">
        <div className="kpi-top">
          <span className="kpi-title">Matched Periods</span>
          <div className="kpi-icon-badge">
            <Layers size={16} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value num-tabular">
            {matched_sample_count?.toLocaleString() || '0'}
          </span>
          <span className="kpi-unit">/ {total_delivery_periods?.toLocaleString() || '0'}</span>
        </div>
        <div className="kpi-footer">
          <span>{coverage_percentage}% settlement coverage</span>
          <span>Hourly stream resolution</span>
        </div>
      </div>

      {/* Optional MAPE Card with zero safeguards */}
      <div className="glass-card kpi-card mape" id="kpi-card-mape">
        <div className="kpi-top">
          <span className="kpi-title">Mean Abs % Error (MAPE)</span>
          <div className="kpi-icon-badge">
            <Percent size={16} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value num-tabular">
            {mape !== null && mape !== undefined ? `${mape.toFixed(1)}%` : '—'}
          </span>
          <span className="kpi-unit">%</span>
        </div>
        <div className="kpi-footer">
          <span>Relative error percentage</span>
          <span style={{ fontSize: '0.72rem' }}>
            {zero_actual_count > 0 ? `${zero_actual_count} zero periods protected` : 'Safe threshold'}
          </span>
        </div>
      </div>
    </div>
  );
}
