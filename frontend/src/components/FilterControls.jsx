import React from 'react';
import { Filter, Calendar, Clock, RotateCcw } from 'lucide-react';

export default function FilterControls({
  cutoffs,
  selectedCutoff,
  onCutoffChange,
  startDate,
  endDate,
  onDateChange,
  onApply,
  onReset,
  loading,
}) {
  const handleQuickRange = (start, end) => {
    onDateChange(start, end);
  };

  return (
    <div className="glass-card control-bar" id="filter-controls">
      <div className="controls-left">
        <div className="control-field">
          <label className="control-label" htmlFor="cutoff-select">
            <Clock size={12} style={{ display: 'inline', marginRight: 4 }} />
            Decision Cutoff
          </label>
          <select
            id="cutoff-select"
            className="select-input"
            value={selectedCutoff}
            onChange={(e) => onCutoffChange(e.target.value)}
            disabled={loading}
          >
            {cutoffs.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-field">
          <label className="control-label" htmlFor="start-date-input">
            <Calendar size={12} style={{ display: 'inline', marginRight: 4 }} />
            Start Date
          </label>
          <input
            id="start-date-input"
            type="date"
            className="date-input"
            value={startDate}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) => onDateChange(e.target.value, endDate)}
            disabled={loading}
          />
        </div>

        <div className="control-field">
          <label className="control-label" htmlFor="end-date-input">
            <Calendar size={12} style={{ display: 'inline', marginRight: 4 }} />
            End Date
          </label>
          <input
            id="end-date-input"
            type="date"
            className="date-input"
            value={endDate}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) => onDateChange(startDate, e.target.value)}
            disabled={loading}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', marginTop: '1.25rem' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => handleQuickRange('2026-01-01', '2026-01-31')}
            title="Whole month of January 2026"
          >
            Full Month
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => handleQuickRange('2026-01-01', '2026-01-07')}
            title="Week 1"
          >
            W1
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => handleQuickRange('2026-01-08', '2026-01-14')}
            title="Week 2"
          >
            W2
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => handleQuickRange('2026-01-15', '2026-01-21')}
            title="Week 3"
          >
            W3
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => handleQuickRange('2026-01-22', '2026-01-31')}
            title="Week 4+"
          >
            W4+
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.65rem' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={onReset}
          disabled={loading}
          title="Reset filters to default"
        >
          <RotateCcw size={14} />
          <span>Reset</span>
        </button>

        <button
          type="button"
          className="btn-primary"
          onClick={onApply}
          disabled={loading}
          id="btn-apply-filters"
        >
          <Filter size={14} />
          <span>{loading ? 'Updating...' : 'Apply Filters'}</span>
        </button>
      </div>
    </div>
  );
}
