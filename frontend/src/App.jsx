import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import DisclosureBanner from './components/DisclosureBanner';
import FilterControls from './components/FilterControls';
import KpiCards from './components/KpiCards';
import TimeSeriesChart from './components/TimeSeriesChart';
import ErrorDistributionChart from './components/ErrorDistributionChart';
import DataTable from './components/DataTable';
import ForecastHistoryModal from './components/ForecastHistoryModal';
import { fetchHealth, fetchCutoffs, fetchForecasts, fetchAccuracy } from './services/api';
import { AlertTriangle, AlertCircle } from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [cutoffs, setCutoffs] = useState([
    { id: 'day_ahead_1200', label: 'Day-Ahead 12:00 UTC (D-1 Auction Reference)' },
    { id: 'day_ahead_1700', label: 'Day-Ahead 17:00 UTC (D-1 Evening Cutoff)' },
    { id: 'day_ahead_2300', label: 'Day-Ahead 23:00 UTC (D-1 Midnight Cutoff)' },
    { id: 'hours_prior_24', label: '24 Hours Prior to Delivery' },
    { id: 'hours_prior_12', label: '12 Hours Prior to Delivery' },
    { id: 'hours_prior_4', label: '4 Hours Prior (Intraday Gate Closure)' },
    { id: 'latest_available', label: 'Latest Available Prior to Delivery (Unrestricted Benchmark)' },
  ]);
  const [selectedCutoff, setSelectedCutoff] = useState('day_ahead_1200');
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState('2026-01-31');

  const [accuracy, setAccuracy] = useState(null);
  const [forecastRecords, setForecastRecords] = useState([]);
  const [selectedInterval, setSelectedInterval] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initial load: health and cutoffs
  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.warn('Could not fetch health:', err));

    fetchCutoffs()
      .then((data) => {
        if (data && data.length) setCutoffs(data);
      })
      .catch((err) => console.warn('Could not fetch cutoffs:', err));
  }, []);

  // Fetch forecast data and accuracy
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [accData, fcData] = await Promise.all([
        fetchAccuracy(startDate, endDate, selectedCutoff),
        fetchForecasts(startDate, endDate, selectedCutoff),
      ]);
      setAccuracy(accData);
      setForecastRecords(fcData.records || []);
    } catch (err) {
      setError(err.message || 'Failed to load wind forecast data');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, selectedCutoff]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleDateChange = (start, end) => {
    setStartDate(start);
    setEndDate(end);
  };

  const handleResetFilters = () => {
    setSelectedCutoff('day_ahead_1200');
    setStartDate('2026-01-01');
    setEndDate('2026-01-31');
  };

  const activeCutoffDesc =
    cutoffs.find((c) => c.id === selectedCutoff)?.label || selectedCutoff;

  return (
    <div className="app-container" id="windsight-app">
      {/* Top Header */}
      <Header health={health} onRefresh={loadDashboardData} loading={loading} />

      {/* Energy Methodology & Disclosures Banner */}
      <DisclosureBanner cutoffDescription={activeCutoffDesc} />

      {/* Filter and Cutoff Selection Controls */}
      <FilterControls
        cutoffs={cutoffs}
        selectedCutoff={selectedCutoff}
        onCutoffChange={setSelectedCutoff}
        startDate={startDate}
        endDate={endDate}
        onDateChange={handleDateChange}
        onApply={loadDashboardData}
        onReset={handleResetFilters}
        loading={loading}
      />

      {/* Global Error Banner */}
      {error && (
        <div
          style={{
            margin: '1.5rem 2rem 0',
            padding: '1rem',
            borderRadius: 8,
            backgroundColor: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state indicator */}
      {loading && (
        <div className="state-container">
          <div className="spinner" />
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Retrieving Elexon actuals & evaluating {activeCutoffDesc}...
          </p>
        </div>
      )}

      {/* Dashboard Main Content */}
      {!loading && (
        <main>
          {/* KPI Summary Cards */}
          <KpiCards accuracy={accuracy} />

          {/* Time Series Charts */}
          <div className="charts-grid">
            <TimeSeriesChart
              records={forecastRecords}
              onSelectInterval={setSelectedInterval}
            />

            <ErrorDistributionChart
              records={forecastRecords}
              onSelectInterval={setSelectedInterval}
            />
          </div>

          {/* Granular Settlement Interval Data Table */}
          <DataTable
            records={forecastRecords}
            onSelectInterval={setSelectedInterval}
          />
        </main>
      )}

      {/* Interactive Forecast Publication Evolution History Modal */}
      {selectedInterval && (
        <ForecastHistoryModal
          deliveryTime={selectedInterval}
          cutoffType={selectedCutoff}
          onClose={() => setSelectedInterval(null)}
        />
      )}
    </div>
  );
}
