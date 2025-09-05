import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { getJSON } from '../lib/api';
import {
  EChartsOption,
  registerLocale,
  registerTheme,
} from 'echarts';

// Register basic components
import 'echarts/lib/chart/line';
import 'echarts/lib/chart/bar';
import 'echarts/lib/chart/pie';
import 'echarts/lib/chart/scatter';
import 'echarts/lib/chart/heatmap';
import 'echarts/lib/chart/gauge';
import 'echarts/lib/chart/radar';
import 'echarts/lib/chart/funnel';
import 'echarts/lib/chart/tree';
import 'echarts/lib/chart/sankey';
import 'echarts/lib/component/grid';
import 'echarts/lib/component/tooltip';
import 'echarts/lib/component/legend';
import 'echarts/lib/component/title';
import 'echarts/lib/component/calendar';
import 'echarts/lib/component/visualMap';

interface ChartData {
  title?: string;
  xAxis?: any; // Can be an array of categories or a configuration object
  yAxis?: any;
  xAxisName?: string;
  yAxisName?: string;
  series?: any[];
  tooltip?: any;
  legend?: any;
  grid?: any;
  calendar?: any;
  calendarRange?: any;
  visualMap?: any;
  data?: any[];
  nodes?: any[];
  links?: any[];
  indicator?: any[];
  indicators?: any[];
  gauges?: any[];
}

interface ChartComponentProps {
  title: string;
  chartData: ChartData | null;
  loading: boolean;
  chartType: string;
}

const ChartComponent: React.FC<ChartComponentProps> = ({ title, chartData, loading, chartType }) => {
  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="flex items-center justify-center h-80">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (!chartData) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="flex items-center justify-center h-80 text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  // Convert backend data to ECharts option
  let option: EChartsOption = {
    title: {
      text: chartData.title || title,
      left: 'center'
    },
    tooltip: chartData.tooltip || { trigger: 'item' },
    legend: chartData.legend || { bottom: 10 },
  };

  // Special handling for different chart types
  switch (chartType) {
    case 'basicLine':
    case 'smoothedLine':
    case 'basicArea':
    case 'stackedArea':
      // FIX: The backend sends an array of categories in `chartData.xAxis`.
      // ECharts requires `xAxis` to be an object where the category array is in the `data` property.
      option = {
        ...option,
        grid: chartData.grid || { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: chartType.includes('Area'), // Improve look for area charts
          data: Array.isArray(chartData.xAxis) ? chartData.xAxis : [],
        },
        yAxis: chartData.yAxis || {
          type: 'value'
        },
        series: chartData.series || []
      };
      break;

    case 'basicScatter':
      option = {
        ...option,
        grid: chartData.grid || { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'value',
          name: chartData.xAxisName || 'X'
        },
        yAxis: {
          type: 'value', 
          name: chartData.yAxisName || 'Y'
        },
        series: chartData.series || []
      };
      break;

    case 'calendarHeatmap':
      option = {
        ...option,
        tooltip: { position: 'top' },
        calendar: chartData.calendar || {
          top: 120,
          left: 30,
          right: 30,
          cellSize: ['auto', 13],
          range: chartData.calendarRange || '2025',
          itemStyle: { borderWidth: 0.5 },
          yearLabel: { show: false }
        },
        visualMap: chartData.visualMap || {
          min: 0,
          max: Math.max(...(chartData.data?.map((item: any) => item[1]) || [100])),
          type: 'piecewise',
          orient: 'horizontal',
          left: 'center',
          top: 65
        },
        series: [{
          type: 'heatmap',
          coordinateSystem: 'calendar',
          data: chartData.data || []
        }]
      };
      break;
    
    case 'multiGauge':
      if (chartData.gauges && Array.isArray(chartData.gauges)) {
        option = {
          ...option,
          series: chartData.gauges.map((gauge: any, index: number) => ({
            type: 'gauge',
            center: [`${25 + (index * 25)}%`, '55%'], // Adjusted vertical position
            radius: '40%',
            detail: { formatter: `{value}${gauge.unit || '%'}` },
            data: [{ value: gauge.value || 0, name: gauge.name || `Gauge ${index + 1}` }],
            title: {
                offsetCenter: [0, '80%'] // Position gauge name below
            },
            max: gauge.max || 100,
            axisLine: {
              lineStyle: {
                width: 15,
                color: [[1, gauge.color || '#007bff']]
              }
            }
          }))
        };
      } else {
        option = {
          ...option,
          series: chartData.series || []
        };
      }
      break;
    
    case 'performanceRadar':
      option = {
        ...option,
        tooltip: { trigger: 'item' },
        legend: {
          data: chartData.data?.map((item: any) => item.name) || [],
          bottom: 10
        },
        radar: {
          indicator: chartData.indicators || chartData.indicator || []
        },
        series: [{
          name: 'Performance Metrics',
          type: 'radar',
          data: chartData.data || chartData.series || []
        }]
      };
      break;

    case 'conversionFunnel':
      option = {
        ...option,
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c}' },
        series: [{
          name: 'Funnel',
          type: 'funnel',
          left: '10%',
          top: 60,
          bottom: 60,
          width: '80%',
          minSize: '0%',
          maxSize: '100%',
          sort: 'descending',
          gap: 2,
          label: {
            show: true,
            position: 'inside'
          },
          labelLine: {
            length: 10,
            lineStyle: {
              width: 1,
              type: 'solid'
            }
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 1
          },
          emphasis: {
            label: {
              fontSize: 20
            }
          },
          data: chartData.data || []
        }]
      };
      break;

    case 'treeHierarchy':
      option = {
        ...option,
        tooltip: { trigger: 'item', triggerOn: 'mousemove' },
        series: [{
          type: 'tree',
          data: chartData.data ? [chartData.data] : [],
          top: '1%',
          left: '7%',
          bottom: '1%',
          right: '20%',
          symbolSize: 7,
          label: {
            position: 'left',
            verticalAlign: 'middle',
            align: 'right',
            fontSize: 9
          },
          leaves: {
            label: {
              position: 'right',
              verticalAlign: 'middle',
              align: 'left'
            }
          },
          emphasis: {
            focus: 'descendant'
          },
          expandAndCollapse: true,
          animationDuration: 550,
          animationDurationUpdate: 750
        } as any]
      };
      break;
    
    case 'sankeyFlow':
      option = {
        ...option,
        tooltip: { trigger: 'item', triggerOn: 'mousemove' },
        series: [{
          type: 'sankey',
          layout: 'none',
          emphasis: {
            focus: 'adjacency'
          },
          data: chartData.nodes || [],
          links: chartData.links || [],
          lineStyle: {
            color: 'gradient',
            curveness: 0.5
          }
        } as any]
      };
      break;

    default:
      // For unhandled chart types, just use series if available
      option = {
        ...option,
        series: chartData.series || []
      };
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-4 text-center">{title}</h3>
      <ReactECharts 
        option={option} 
        style={{ height: '400px', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
};

export default function AdvancedChartsPage() {
  const [chartData, setChartData] = useState<Record<string, ChartData | null>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const charts = [
      { key: 'basicLine', endpoint: '/advanced-charts/line-charts/basic', title: 'Basic Line Chart' },
      { key: 'smoothedLine', endpoint: '/advanced-charts/line-charts/smoothed', title: 'Smoothed Line Chart' },
      { key: 'basicArea', endpoint: '/advanced-charts/area-charts/basic', title: 'Basic Area Chart' },
      { key: 'stackedArea', endpoint: '/advanced-charts/area-charts/stacked', title: 'Stacked Area Chart' },
      { key: 'basicScatter', endpoint: '/advanced-charts/scatter-charts/basic', title: 'Scatter Plot' },
      { key: 'calendarHeatmap', endpoint: '/advanced-charts/heatmap-charts/calendar', title: 'Calendar Heatmap' },
      { key: 'multiGauge', endpoint: '/advanced-charts/gauge-charts/multi', title: 'Multi Gauge Chart' },
      { key: 'performanceRadar', endpoint: '/advanced-charts/radar-charts/performance', title: 'Performance Radar' },
      { key: 'conversionFunnel', endpoint: '/advanced-charts/funnel-charts/conversion', title: 'Conversion Funnel' },
      { key: 'treeHierarchy', endpoint: '/advanced-charts/tree-charts/hierarchy', title: 'Tree Hierarchy' },
      { key: 'sankeyFlow', endpoint: '/advanced-charts/sankey-charts/flow', title: 'Sankey Flow Diagram' }
    ];

    const loadChartData = async () => {
      // Set initial loading states
      const initialLoading = charts.reduce((acc, chart) => {
        acc[chart.key] = true;
        return acc;
      }, {} as Record<string, boolean>);
      setLoading(initialLoading);

      // Load all charts
      for (const chart of charts) {
        try {
          const data = await getJSON<ChartData>(chart.endpoint);
          setChartData(prev => ({ ...prev, [chart.key]: data }));
        } catch (error) {
          console.error(`Failed to load ${chart.title}:`, error);
          setChartData(prev => ({ ...prev, [chart.key]: null }));
        } finally {
          setLoading(prev => ({ ...prev, [chart.key]: false }));
        }
      }
    };
    
    loadChartData();
  }, []);

  const chartConfigs = [
    { key: 'basicLine', title: 'Basic Line Chart', type: 'basicLine' },
    { key: 'smoothedLine', title: 'Smoothed Line Chart', type: 'smoothedLine' },
    { key: 'basicArea', title: 'Basic Area Chart', type: 'basicArea' },
    { key: 'stackedArea', title: 'Stacked Area Chart', type: 'stackedArea' },
    { key: 'basicScatter', title: 'Scatter Plot', type: 'basicScatter' },
    { key: 'calendarHeatmap', title: 'Calendar Heatmap', type: 'calendarHeatmap' },
    { key: 'multiGauge', title: 'Multi Gauge Chart', type: 'multiGauge' },
    { key: 'performanceRadar', title: 'Performance Radar', type: 'performanceRadar' },
    { key: 'conversionFunnel', title: 'Conversion Funnel', type: 'conversionFunnel' },
    { key: 'treeHierarchy', title: 'Tree Hierarchy', type: 'treeHierarchy' },
    { key: 'sankeyFlow', title: 'Sankey Flow Diagram', type: 'sankeyFlow' }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Advanced ECharts Dashboard</h1>
          <p className="text-gray-600">Comprehensive visualization of all chart types using MongoDB data</p>
        </div>

        {/* Navigation */}
        <div className="mb-8 flex gap-4">
          <a href="/" className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
            Home
          </a>
          <a href="/working-dashboard" className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
            Working Dashboard
          </a>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {chartConfigs.map(chart => (
            <ChartComponent
              key={chart.key}
              title={chart.title}
              chartData={chartData[chart.key]}
              loading={loading[chart.key]}
              chartType={chart.type}
            />
          ))}
        </div>
      </div>
    </div>
  );
}