import React, { useState } from 'react';
import { Info, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

export default function DisclosureBanner({ cutoffDescription }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="disclosure-banner" id="disclosure-banner">
      <Info size={20} className="disclosure-icon" />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="disclosure-text">
            <strong>Active Decision Cutoff:</strong> {cutoffDescription || 'Day-Ahead 12:00 UTC'}
            &nbsp;•&nbsp;
            <span>
              Evaluates the latest eligible forecast published at or before the day-ahead gate closure.
            </span>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: 'none',
              border: 'none',
              color: '#38bdf8',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
            }}
          >
            {expanded ? 'Hide Disclosures' : 'View Methodology & Disclosures'}
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        {expanded && (
          <div style={{ marginTop: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <ul style={{ listStyleType: 'disc', paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.6 }}>
              <li>
                <strong>Procurement Volume & Cost Boundaries:</strong> While this dashboard quantifies generation forecast errors ($F_t - A_t$), it explicitly does not calculate procurement volumes, open imbalance positions, or financial imbalance costs. Calculating those requires national power demand, market settlement prices (System Buy/Sell Prices), and thermal unit dispatch data, which are not provided in Elexon's FUELHH/WINDFOR streams.
              </li>
              <li>
                <strong>Day-Ahead Decision Cutoff Selection:</strong> For every delivery interval $T$ on delivery date $D$, only forecasts published at or before the designated cutoff timestamp (e.g. $D-1$ 12:00:00 UTC) are eligible. Among all eligible submissions, the latest published forecast is selected. Post-cutoff intraday forecasts are never substituted silently.
              </li>
              <li>
                <strong>Data Source & Resolution Disclosure:</strong> Actuals are sourced from Elexon BMRS <code>FUELHH/stream</code> (half-hourly outturn for fuelType WIND). Forecasts are sourced from <code>WINDFOR/stream</code> (hourly delivery resolution). Records are matched strictly on delivery <code>startTime</code>.
              </li>
              <li>
                <strong>Timezone Integrity:</strong> All timestamps are ingested and processed in UTC internally and converted to UK Local Time (GMT in January) for display.
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
