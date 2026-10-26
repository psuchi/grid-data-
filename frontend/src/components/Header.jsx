import React from 'react';
import { Wind, Clock, Database, RefreshCw, AlertCircle } from 'lucide-react';

export default function Header({ health, onRefresh, loading }) {
  const isSynthetic = health?.isSynthetic ?? false;
  const dataSource = health?.dataSource || 'Connecting to Elexon...';

  return (
    <header className="header-container" id="windsight-header">
      <div className="brand-wrapper">
        <div className="brand-icon-box">
          <Wind size={26} />
        </div>
        <div>
          <h1 className="brand-title">WindSight</h1>
          <p className="brand-subtitle">
            Historical January 2026 UK Wind Forecast Monitoring & Day-Ahead Accuracy
          </p>
        </div>
      </div>

      <div className="header-status-group">
        <div className="status-badge" title="UK local time in January is Greenwich Mean Time (UTC+0)">
          <Clock size={14} style={{ color: '#38bdf8' }} />
          <span>UK Local (GMT / UTC)</span>
        </div>

        <div className={`status-badge ${isSynthetic ? 'synthetic' : ''}`} title={`Data source: ${dataSource}`}>
          <div className="status-indicator-dot" />
          <Database size={14} />
          <span>{dataSource}</span>
        </div>

        <button
          className="btn-secondary"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh Data"
          id="btn-refresh-data"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>
    </header>
  );
}
