import { useMemo, useState } from 'react';
import useSWR from 'swr';
import EChart from '../components/EChart';
import { getJSON } from '../lib/api';

type QueryPayload = any;

function useAnalytics(payload: QueryPayload | null) {
  const key = payload ? ['/v1/analytics/query', JSON.stringify(payload)] : null as any;
  return useSWR(key, ([p,_]) => fetch('/api/v1/analytics/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).then(r => r.json()));
}

export default function Gallery() {
  const [dataset, setDataset] = useState<string>('timerlogs');
  const [chart, setChart] = useState<string>('line');

  // contoh payload generik untuk beberapa chart
  const payload = useMemo(() => {
    if (dataset === 'timerlogs' && chart === 'line') {
      return {
        collection: 'timerlogs',
        filters: { timeField: 'createdAt' },
        group: { timeBucket: 'day', timeField: 'createdAt', by: [] },
        metrics: [{ op: 'count', field: '_id', as: 'events' }],
        limit: 1000,
      };
    }
    if (dataset === 'counts' && chart === 'stacked-line') {
      return {
        collection: 'counts',
        filters: { timeField: 'startAt' },
        group: { timeBucket: 'day', timeField: 'startAt', by: ['timerId'] },
        metrics: [{ op: 'sum', field: 'tons', as: 'tons' }],
        limit: 1000,
      };
    }
    if (dataset === 'timerlogs' && chart === 'pareto') {
      return null; // pakai endpoint khusus pareto di bawah
    }
    return {
      collection: dataset,
      filters: { timeField: 'createdAt' },
      group: { timeBucket: 'day', timeField: 'createdAt', by: [] },
      metrics: [{ op: 'count', field: '_id', as: 'count' }],
      limit: 365,
    };
  }, [dataset, chart]);

  const { data } = useAnalytics(payload);
  const { data: pareto } = useSWR(chart === 'pareto' ? '/v1/analytics/timerlogs/pareto/stop-reasons' : null, (p) => getJSON(p));
  const { data: heat } = useSWR(chart === 'calendar' ? '/v1/analytics/timerlogs/heatmap/daily-counts' : null, (p) => getJSON(p));

  const option = useMemo(() => {
    if (chart === 'pareto' && pareto) {
      const items = pareto.items || [];
      return {
        tooltip: {},
        title: { text: 'Pareto Stop Reasons' },
        grid: { left: 150, right: 20 },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: items.map((i: any) => i.stopReason) },
        series: [{ type: 'bar', data: items.map((i: any) => i.count) }],
      };
    }
    if (chart === 'calendar' && heat) {
      const items = heat.items || [];
      return {
        tooltip: {},
        title: { text: 'Events per Day (Timerlogs)' },
        visualMap: { min: 0, max: Math.max(...items.map((i: any) => i.count), 10), orient: 'horizontal' },
        calendar: { range: items.length ? items[0].day.substring(0,4) : '2024' },
        series: [{ type: 'heatmap', coordinateSystem: 'calendar', data: items.map((i: any) => [i.day, i.count]) }],
      };
    }
    if (!data) return { title: { text: 'Loading...' } } as any;
    const cols: string[] = data.columns || [];
    const rows: any[] = data.rows || [];
    const tIndex = cols.indexOf('t');
    const catCols = cols.filter((c: string) => c !== 't' && c !== 'count' && c !== 'events' && c !== 'tons' && c !== 'duration');
    const metric = ['tons', 'events', 'count', 'duration'].find((m) => cols.includes(m)) || cols[cols.length - 1];
    const categories = Array.from(new Set(rows.map((r: any) => (tIndex >= 0 ? r[tIndex] : ''))));
    const seriesBy = data.raw && data.raw.length && typeof data.raw[0]._id === 'object' ? Object.keys(data.raw[0]._id).filter((k: string) => k !== 't')[0] : undefined;
    const groups = seriesBy ? Array.from(new Set(data.raw.map((r: any) => r._id[seriesBy] ?? 'Unknown'))) : ['Series'];
    const series = groups.map((g: any) => ({
      type: chart.includes('area') ? 'line' : 'line',
      name: String(g),
      areaStyle: chart.includes('area') ? {} : undefined,
      stack: chart.includes('stacked') ? 'stack' : undefined,
      showSymbol: false,
      data: categories.map((c) => {
        const found = rows.find((r: any, idx: number) => (tIndex >= 0 ? r[tIndex] === c : true) && (!seriesBy || data.raw[idx]._id[seriesBy] === g));
        const mIndex = cols.indexOf(metric);
        return found ? found[mIndex] : 0;
      })
    }));
    return {
      tooltip: { trigger: 'axis' },
      title: { text: `${dataset} - ${chart}` },
      legend: {},
      xAxis: { type: 'category', data: categories },
      yAxis: { type: 'value' },
      series,
    };
  }, [data, chart, dataset, pareto, heat]);

  return (
    <div style={{ padding: 16 }}>
      <h2>ECharts Gallery (APMS)</h2>
      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <label>
          Dataset:&nbsp;
          <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
            <option value="timerlogs">timerlogs</option>
            <option value="counts">counts</option>
            <option value="cycletimers">cycletimers</option>
            <option value="timerdailystats">timerdailystats</option>
          </select>
        </label>
        <label>
          Chart:&nbsp;
          <select value={chart} onChange={(e) => setChart(e.target.value)}>
            <option value="line">Basic Line</option>
            <option value="stacked-line">Stacked Line</option>
            <option value="area">Basic Area</option>
            <option value="stacked-area">Stacked Area</option>
            <option value="pareto">Pareto (Bar)</option>
            <option value="calendar">Calendar Heatmap</option>
          </select>
        </label>
      </div>
      <EChart option={option} />
    </div>
  );
}

