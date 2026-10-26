import React, { useState, useMemo } from 'react';
import { Search, Download, ArrowUpDown, ChevronLeft, ChevronRight, Eye } from 'lucide-react';

export default function DataTable({ records, onSelectInterval }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMode, setFilterMode] = useState('all'); // 'all', 'matched', 'unmatched'
  const [sortField, setSortField] = useState('startTimeUtc');
  const [sortAsc, setSortAsc] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const filteredRecords = useMemo(() => {
    if (!records) return [];

    return records.filter((r) => {
      // Filter mode
      if (filterMode === 'matched' && !r.isMatched) return false;
      if (filterMode === 'unmatched' && r.isMatched) return false;

      // Search term
      if (!searchTerm) return true;
      const term = searchTerm.toLowerCase();
      return (
        r.startTimeLocal?.toLowerCase().includes(term) ||
        r.settlementDate?.toLowerCase().includes(term) ||
        r.settlementPeriod?.toString().includes(term) ||
        r.publishTimeLocal?.toLowerCase().includes(term)
      );
    });
  }, [records, filterMode, searchTerm]);

  const sortedRecords = useMemo(() => {
    return [...filteredRecords].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (valA === null || valA === undefined) return sortAsc ? 1 : -1;
      if (valB === null || valB === undefined) return sortAsc ? -1 : 1;

      if (typeof valA === 'string') {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? valA - valB : valB - valA;
    });
  }, [filteredRecords, sortField, sortAsc]);

  const totalPages = Math.ceil(sortedRecords.length / pageSize) || 1;
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedRecords.slice(start, start + pageSize);
  }, [sortedRecords, currentPage, pageSize]);

  const exportCSV = () => {
    if (!sortedRecords.length) return;
    const headers = [
      'Delivery Interval (GMT)',
      'Settlement Date',
      'Settlement Period',
      'Actual Gen (MW)',
      'Selected Forecast (MW)',
      'Publish Time (GMT)',
      'Lead Time (hrs)',
      'Signed Error (MW)',
      'Absolute Error (MW)',
      'Matched Status',
    ];

    const rows = sortedRecords.map((r) => [
      r.startTimeLocal,
      r.settlementDate,
      r.settlementPeriod,
      r.actualMw !== null ? r.actualMw : '',
      r.forecastMw !== null ? r.forecastMw : '',
      r.publishTimeLocal || '',
      r.leadTimeHours !== null ? r.leadTimeHours : '',
      r.signedErrorMw !== null ? r.signedErrorMw : '',
      r.absoluteErrorMw !== null ? r.absoluteErrorMw : '',
      r.isMatched ? 'Matched' : 'Unforecasted at Cutoff',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `windsight_wind_forecasts_${new Date().toISOString().substring(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="glass-card table-section" id="data-table-section">
      <div className="table-header-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            Settlement Interval Records
          </h2>
          <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
            Showing {filteredRecords.length.toLocaleString()} intervals
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Search Input */}
          <div style={{ position: 'relative' }}>
            <Search
              size={14}
              style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }}
            />
            <input
              type="text"
              className="table-search-input"
              placeholder="Filter by date or SP..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              style={{ paddingLeft: '2rem' }}
            />
          </div>

          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '0.25rem', background: 'rgba(255,255,255,0.04)', padding: 3, borderRadius: 6 }}>
            <button
              className={`page-btn ${filterMode === 'all' ? 'active' : ''}`}
              style={{
                backgroundColor: filterMode === 'all' ? '#0284c7' : 'transparent',
                border: 'none',
              }}
              onClick={() => {
                setFilterMode('all');
                setCurrentPage(1);
              }}
            >
              All
            </button>
            <button
              className={`page-btn ${filterMode === 'matched' ? 'active' : ''}`}
              style={{
                backgroundColor: filterMode === 'matched' ? '#0284c7' : 'transparent',
                border: 'none',
              }}
              onClick={() => {
                setFilterMode('matched');
                setCurrentPage(1);
              }}
            >
              Matched
            </button>
            <button
              className={`page-btn ${filterMode === 'unmatched' ? 'active' : ''}`}
              style={{
                backgroundColor: filterMode === 'unmatched' ? '#0284c7' : 'transparent',
                border: 'none',
              }}
              onClick={() => {
                setFilterMode('unmatched');
                setCurrentPage(1);
              }}
            >
              Unmatched
            </button>
          </div>

          {/* Export Button */}
          <button className="btn-secondary" onClick={exportCSV} title="Export filtered records to CSV">
            <Download size={14} />
            <span>CSV Export</span>
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('startTimeUtc')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  Delivery Time (GMT) <ArrowUpDown size={12} />
                </div>
              </th>
              <th>SP</th>
              <th onClick={() => handleSort('actualMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  Actual (MW) <ArrowUpDown size={12} />
                </div>
              </th>
              <th onClick={() => handleSort('forecastMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  Selected FC (MW) <ArrowUpDown size={12} />
                </div>
              </th>
              <th>Publication Time</th>
              <th>Lead Time</th>
              <th onClick={() => handleSort('signedErrorMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  Signed Error <ArrowUpDown size={12} />
                </div>
              </th>
              <th onClick={() => handleSort('absoluteErrorMw')} style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  Abs Error <ArrowUpDown size={12} />
                </div>
              </th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {paginatedRecords.length > 0 ? (
              paginatedRecords.map((r, i) => (
                <tr
                  key={i}
                  onClick={() => onSelectInterval(r.startTimeUtc)}
                  title="Click to view forecast evolution history"
                >
                  <td className="highlight">{r.startTimeLocal}</td>
                  <td className="num-tabular">{r.settlementPeriod}</td>
                  <td className="num-tabular" style={{ color: '#06b6d4', fontWeight: 600 }}>
                    {r.actualMw !== null ? r.actualMw.toLocaleString() : 'N/A'}
                  </td>
                  <td className="num-tabular" style={{ color: '#818cf8', fontWeight: 600 }}>
                    {r.forecastMw !== null ? r.forecastMw.toLocaleString() : '—'}
                  </td>
                  <td>{r.publishTimeLocal || '—'}</td>
                  <td className="num-tabular">{r.leadTimeHours !== null ? `${r.leadTimeHours}h` : '—'}</td>
                  <td className="num-tabular">
                    {r.signedErrorMw !== null ? (
                      <span className={`error-cell ${r.signedErrorMw > 0 ? 'positive' : 'negative'}`}>
                        {r.signedErrorMw > 0 ? `+${r.signedErrorMw.toLocaleString()}` : r.signedErrorMw.toLocaleString()}
                      </span>
                    ) : (
                      <span className="error-cell neutral">—</span>
                    )}
                  </td>
                  <td className="num-tabular">
                    {r.absoluteErrorMw !== null ? r.absoluteErrorMw.toLocaleString() : '—'}
                  </td>
                  <td>
                    <span
                      style={{
                        display: 'inline-flex',
                        padding: '2px 8px',
                        borderRadius: 9999,
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        backgroundColor: r.isMatched ? 'rgba(16, 185, 129, 0.15)' : 'rgba(100, 116, 139, 0.15)',
                        color: r.isMatched ? '#34d399' : '#94a3b8',
                      }}
                    >
                      {r.isMatched ? 'Matched' : 'Unforecasted'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn-secondary"
                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectInterval(r.startTimeUtc);
                      }}
                      title="View publication history"
                    >
                      <Eye size={12} />
                      <span>History</span>
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '2.5rem', color: '#94a3b8' }}>
                  No settlement records match your criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="pagination-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>Rows per page:</span>
          <select
            className="select-input"
            style={{ padding: '0.2rem 0.5rem', fontSize: '0.78rem' }}
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
          >
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span style={{ marginLeft: '0.75rem' }}>
            Page {currentPage} of {totalPages}
          </span>
        </div>

        <div className="pagination-controls">
          <button
            className="page-btn"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft size={14} style={{ display: 'inline' }} /> Prev
          </button>
          <button
            className="page-btn"
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          >
            Next <ChevronRight size={14} style={{ display: 'inline' }} />
          </button>
        </div>
      </div>
    </div>
  );
}
