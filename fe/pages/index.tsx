import { useMemo, useState } from 'react';
import Link from 'next/link';
import useSWR from 'swr';
import EChart from '../components/EChart';
import { getJSON } from '../lib/api';

type ProdSummary = { items: { timerId?: string; totalTons: number; avgRunRate?: number; avgTargetRate?: number; counts: number }[] };
type Downtime = { items: { stopReason: string; totalDurationSec: number }[] };
type CycleTimes = { items: { t: string; cycleSec: number }[] };
type Utilization = { items: { day: string; runSec: number; stopSec: number; runPct: number; stopPct: number }[] };
type RunrateTS = { items: { day: string; runRate: number; targetRate: number; n: number }[] };
type Refs = { locations: { _id: string; name?: string }[]; machineclasses: { _id: string; name?: string }[] };

export default function Home() {
  const [locationId, setLocationId] = useState<string>('');
  const params = useMemo(() => (locationId ? { location_id: locationId } : {}), [locationId]);

  const { data: prod } = useSWR<ProdSummary>(['/v1/production/summary', params], ([p, q]) => getJSON(p, q));
  const { data: dt } = useSWR<Downtime>(['/v1/downtime/reasons', params], ([p, q]) => getJSON(p, q));
  const { data: cycles } = useSWR<CycleTimes>(['/v1/cycle-times', {}], ([p, q]) => getJSON(p, q));
  const { data: util } = useSWR<Utilization>(['/v1/utilization/daily', params], ([p, q]) => getJSON(p, q));
  const { data: rr } = useSWR<RunrateTS>(['/v1/production/runrate-timeseries', params], ([p, q]) => getJSON(p, q));
  const { data: refs } = useSWR<Refs>('/v1/refs/basic', (p) => getJSON(p));

  const locOptions = useMemo(() => refs?.locations ?? [], [refs]);
  const locName = useMemo(() => locOptions.find(l => l._id === locationId)?.name ?? locationId, [locOptions, locationId]);

  const productionOption = useMemo(() => {
    const items = prod?.items ?? [];
    return {
      tooltip: {},
      title: { text: 'Total Tons per Timer' },
      xAxis: { type: 'category', data: items.map((i) => i.timerId ?? 'unknown') },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: items.map((i) => i.totalTons) }],
    };
  }, [prod]);

  const downtimeOption = useMemo(() => {
    const items = dt?.items ?? [];
    return {
      tooltip: {},
      title: { text: 'Downtime by Reason (sec)' },
      grid: { left: 120, right: 20 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: items.map((i) => i.stopReason) },
      series: [{ type: 'bar', data: items.map((i) => Math.round(i.totalDurationSec)) }],
    };
  }, [dt]);

  const cyclesOption = useMemo(() => {
    const items = cycles?.items ?? [];
    return {
      tooltip: {},
      title: { text: 'Cycle Times' },
      xAxis: { type: 'time' },
      yAxis: { type: 'value', name: 'sec' },
      series: [
        {
          type: 'line',
          showSymbol: false,
          data: items.map((i) => [i.t, i.cycleSec]),
        },
      ],
    };
  }, [cycles]);

  const utilizationOption = useMemo(() => {
    const items = util?.items ?? [];
    return {
      tooltip: { trigger: 'axis' },
      title: { text: `Utilization per Day${locName ? ` (${locName})` : ''}` },
      legend: { data: ['Run %', 'Stop %'] },
      xAxis: { type: 'category', data: items.map((i) => i.day) },
      yAxis: { type: 'value', name: '%', max: 100 },
      series: [
        { type: 'line', name: 'Run %', data: items.map((i) => i.runPct) },
        { type: 'line', name: 'Stop %', data: items.map((i) => i.stopPct) },
      ],
    };
  }, [util, locName]);

  const runrateOption = useMemo(() => {
    const items = rr?.items ?? [];
    return {
      tooltip: { trigger: 'axis' },
      title: { text: `RunRate vs TargetRate${locName ? ` (${locName})` : ''}` },
      legend: { data: ['RunRate', 'TargetRate'] },
      xAxis: { type: 'category', data: items.map((i) => i.day) },
      yAxis: { type: 'value' },
      series: [
        { type: 'line', name: 'RunRate', data: items.map((i) => i.runRate) },
        { type: 'line', name: 'TargetRate', data: items.map((i) => i.targetRate) },
      ],
    };
  }, [rr, locName]);

  return (
    <div style={{ padding: 16, fontFamily: 'sans-serif' }}>
      <h2>APMS Dashboard</h2>
      <div style={{ marginBottom: 12, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <label>
          Location:&nbsp;
          <select value={locationId} onChange={(e) => setLocationId(e.target.value)}>
            <option value="">All</option>
            {locOptions.map((l) => (
              <option key={l._id} value={l._id}>{l.name ?? l._id}</option>
            ))}
          </select>
        </label>
        <Link href="/working-dashboard" style={{ 
          background: '#28a745', 
          color: 'white', 
          padding: '8px 16px', 
          textDecoration: 'none', 
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          📊 Working Dashboard
        </Link>
        <Link href="/advanced-charts" style={{ 
          background: '#17a2b8', 
          color: 'white', 
          padding: '8px 16px', 
          textDecoration: 'none', 
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          📈 Advanced Charts
        </Link>
        <Link href="/comprehensive-dashboard" style={{ 
          background: '#007bff', 
          color: 'white', 
          padding: '8px 16px', 
          textDecoration: 'none', 
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          🚀 Full Comprehensive Dashboard
        </Link>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
        <EChart option={productionOption} />
        <EChart option={downtimeOption} />
        <EChart option={cyclesOption} />
        <EChart option={utilizationOption} />
        <EChart option={runrateOption} />
      </div>
    </div>
  );
}
