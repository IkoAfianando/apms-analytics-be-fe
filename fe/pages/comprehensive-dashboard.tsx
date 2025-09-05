import { useState, useEffect } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import {
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  GaugeChart,
  RadarChart,
  FunnelChart,
  SunburstChart,
  TreemapChart,
  GraphChart,
  SankeyChart,
  CandlestickChart,
  BoxplotChart,
  ParallelChart,
  ThemeRiverChart,
  CustomChart,
  TreeChart
} from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  BrushComponent,
  TitleComponent,
  TimelineComponent,
  MarkPointComponent,
  MarkLineComponent,
  MarkAreaComponent,
  CalendarComponent,
  GraphicComponent,
  ToolboxComponent,
  VisualMapComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { getJSON } from '../lib/api';

// Register the required components
echarts.use([
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  GaugeChart,
  RadarChart,
  FunnelChart,
  SunburstChart,
  TreemapChart,
  GraphChart,
  SankeyChart,
  CandlestickChart,
  BoxplotChart,
  ParallelChart,
  ThemeRiverChart,
  CustomChart,
  TreeChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  BrushComponent,
  TitleComponent,
  TimelineComponent,
  MarkPointComponent,
  MarkLineComponent,
  MarkAreaComponent,
  CalendarComponent,
  GraphicComponent,
  ToolboxComponent,
  VisualMapComponent,
  CanvasRenderer
]);

interface ChartData {
  xAxis?: string[];
  series?: any[];
  data?: any[];
  [key: string]: any;
}

interface DashboardData {
  production: {
    totalProduced: number;
    totalLogs: number;
    efficiency: number;
    avgCycleTime: number;
    uniqueTimers: number;
    uniqueMachines: number;
  };
  oee: {
    overall: number;
    availability: number;
    performance: number;
    quality: number;
    efficiency: number;
  };
  machines: {
    total: number;
    active: number;
    inactive: number;
    maintenance: number;
  };
  downtime: {
    total: number;
  };
}

const ChartComponent = ({ title, data, type = 'line', style = {} }: {
  title: string;
  data: ChartData;
  type?: string;
  style?: React.CSSProperties;
}) => {
  const getOption = () => {
    const baseOption = {
      title: {
        text: title,
        left: 'center'
      },
      tooltip: {
        trigger: type === 'pie' ? 'item' : 'axis'
      },
      legend: {
        top: 'bottom'
      }
    };

    // Add error handling for missing data
    if (!data) {
      return {
        ...baseOption,
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: {
            text: 'No data available',
            fontSize: 16,
            fill: '#999'
          }
        }
      };
    }

    switch (type) {
      case 'line':
        return {
          ...baseOption,
          xAxis: {
            type: 'category',
            data: data.xAxis || []
          },
          yAxis: {
            type: 'value'
          },
          series: data.series || []
        };

      case 'bar':
        return {
          ...baseOption,
          xAxis: {
            type: 'category',
            data: data.xAxis || []
          },
          yAxis: {
            type: 'value'
          },
          series: data.series || []
        };

      case 'pie':
        return {
          ...baseOption,
          series: [
            {
              name: title,
              type: 'pie',
              radius: '50%',
              data: data.data || [],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        };

      case 'gauge':
        return {
          ...baseOption,
          series: [
            {
              name: title,
              type: 'gauge',
              detail: { formatter: '{value}%' },
              data: [{ value: data.value || 0, name: title }],
              max: data.max || 100
            }
          ]
        };

      case 'heatmap':
        // Check if this is a calendar heatmap
        if (data.calendarRange) {
          return {
            ...baseOption,
            calendar: {
              top: 120,
              left: 30,
              right: 30,
              cellSize: ['auto', 13],
              range: data.calendarRange || ['2025-01-01', '2025-12-31'],
              itemStyle: {
                borderWidth: 0.5
              },
              yearLabel: { show: false }
            },
            visualMap: {
              min: 0,
              max: Math.max(...(data.data?.map((item: any) => item[1]) || [100])),
              type: 'piecewise',
              orient: 'horizontal',
              left: 'center',
              top: 65
            },
            series: [
              {
                name: title,
                type: 'heatmap',
                coordinateSystem: 'calendar',
                data: data.data || []
              }
            ]
          };
        } else {
          // Regular heatmap
          return {
            ...baseOption,
            xAxis: {
              type: 'category',
              data: data.xAxis || []
            },
            yAxis: {
              type: 'category',
              data: data.yAxis || []
            },
            visualMap: {
              min: 0,
              max: 100,
              calculable: true,
              orient: 'horizontal',
              left: 'center',
              bottom: '15%'
            },
            series: [
              {
                name: title,
                type: 'heatmap',
                data: data.data || [],
                label: {
                  show: true
                },
                emphasis: {
                  itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                  }
                }
              }
            ]
          };
        }

      case 'radar':
        return {
          ...baseOption,
          radar: {
            indicator: data.data?.map((item: any) => ({
              name: item.name,
              max: item.max || 100
            })) || []
          },
          series: [
            {
              name: title,
              type: 'radar',
              data: [
                {
                  value: data.data?.map((item: any) => item.value) || [],
                  name: title
                }
              ]
            }
          ]
        };

      case 'scatter':
        return {
          ...baseOption,
          xAxis: {
            type: 'value',
            name: data.xAxisName || 'X'
          },
          yAxis: {
            type: 'value',
            name: data.yAxisName || 'Y'
          },
          series: data.series || []
        };

      default:
        return {
          ...baseOption,
          graphic: {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: `Chart type "${type}" not supported`,
              fontSize: 16,
              fill: '#999'
            }
          }
        };
    }
  };

  return (
    <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px', ...style }}>
      <ReactEChartsCore
        echarts={echarts}
        option={getOption()}
        style={{ height: '400px', width: '100%' }}
      />
    </div>
  );
};

export default function ComprehensiveDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [charts, setCharts] = useState<{ [key: string]: ChartData }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Test API connection first
        console.log('Testing API connection...');
        const healthCheck = await getJSON<{ ok: boolean }>('/health');
        console.log('Health check result:', healthCheck);

        // Load dashboard overview
        console.log('Loading dashboard overview...');
        const overview = await getJSON<DashboardData>('/simple-dashboard/overview');
        console.log('Dashboard overview:', overview);
        setDashboardData(overview);

        // Load chart data in parallel
        const chartPromises = [
          getJSON<ChartData>('/advanced-charts/line-charts/basic').then(data => ({ type: 'basicLine', data })),
          getJSON<ChartData>('/advanced-charts/line-charts/smoothed').then(data => ({ type: 'smoothedLine', data })),
          getJSON<ChartData>('/advanced-charts/area-charts/basic').then(data => ({ type: 'basicArea', data })),
          getJSON<ChartData>('/advanced-charts/area-charts/stacked').then(data => ({ type: 'stackedArea', data })),
          getJSON<ChartData>('/advanced-charts/scatter-charts/basic').then(data => ({ type: 'basicScatter', data })),
          getJSON<ChartData>('/advanced-charts/heatmap-charts/calendar').then(data => ({ type: 'calendarHeatmap', data })),
          getJSON<ChartData>('/advanced-charts/gauge-charts/multi').then(data => ({ type: 'multiGauge', data })),
          getJSON<ChartData>('/advanced-charts/radar-charts/performance').then(data => ({ type: 'performanceRadar', data })),
          getJSON<ChartData>('/advanced-charts/funnel-charts/conversion').then(data => ({ type: 'conversionFunnel', data })),
          getJSON<ChartData>('/advanced-charts/tree-charts/hierarchy').then(data => ({ type: 'treeHierarchy', data })),
          getJSON<ChartData>('/advanced-charts/sankey-charts/flow').then(data => ({ type: 'sankeyFlow', data })),
          getJSON<ChartData>('/simple-dashboard/overview').then(data => ({ type: 'overview', data }))
        ];

        const chartResults = await Promise.allSettled(chartPromises);
        const newCharts: { [key: string]: ChartData } = {};

        chartResults.forEach((result, index) => {
          if (result.status === 'fulfilled') {
            newCharts[result.value.type] = result.value.data;
          } else {
            console.error(`Chart ${index} failed:`, result.reason);
          }
        });

        setCharts(newCharts);
      } catch (err) {
        console.error('Error loading dashboard:', err);
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading comprehensive dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>
        Comprehensive APMS Analytics Dashboard
      </h1>

      {/* KPI Cards */}
      {dashboardData && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
            <h3>Production</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff' }}>
              {dashboardData.production.totalProduced}
            </div>
            <div>Units Produced</div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>
              Efficiency: {dashboardData.production.efficiency}%
            </div>
          </div>

          <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
            <h3>OEE</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
              {dashboardData.oee.overall}%
            </div>
            <div>Overall Equipment Effectiveness</div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>
              A: {dashboardData.oee.availability}% | P: {dashboardData.oee.performance}% | Q: {dashboardData.oee.quality}%
            </div>
          </div>

          <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
            <h3>Machines</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#17a2b8' }}>
              {dashboardData.machines.active}/{dashboardData.machines.total}
            </div>
            <div>Active Machines</div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>
              Inactive: {dashboardData.machines.inactive}
            </div>
          </div>

          <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
            <h3>Downtime</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
              {dashboardData.downtime.total}h
            </div>
            <div>Total Downtime</div>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px' }}>
        
        {/* Basic Line Chart */}
        {charts.basicLine && charts.basicLine.xAxis && charts.basicLine.series && (
          <ChartComponent
            title="Daily Production Units"
            data={charts.basicLine}
            type="line"
          />
        )}

        {/* Smoothed Line Chart */}
        {charts.smoothedLine && charts.smoothedLine.xAxis && charts.smoothedLine.series && (
          <ChartComponent
            title="Production vs Downtime Trend"
            data={charts.smoothedLine}
            type="line"
          />
        )}

        {/* Basic Area Chart */}
        {charts.basicArea && charts.basicArea.xAxis && charts.basicArea.series && (
          <ChartComponent
            title="Activity by Location"
            data={{
              xAxis: charts.basicArea.xAxis,
              series: charts.basicArea.series?.map((s: any) => ({
                ...s,
                type: 'line' // Change from 'area' to 'line'
              }))
            }}
            type="line"
          />
        )}

        {/* Basic Scatter Chart */}
        {charts.basicScatter && charts.basicScatter.series && (
          <ChartComponent
            title="Cycle Time vs Hour of Day"
            data={charts.basicScatter}
            type="scatter"
          />
        )}

        {/* Calendar Heatmap */}
        {charts.calendarHeatmap && charts.calendarHeatmap.data && (
          <ChartComponent
            title="Production Calendar Heatmap"
            data={charts.calendarHeatmap}
            type="heatmap"
          />
        )}

        {/* Multi Gauge */}
        {charts.multiGauge && charts.multiGauge.gauges && (
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>Performance Gauges</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '20px' }}>
              {charts.multiGauge.gauges.map((gauge: any, index: number) => (
                <ChartComponent
                  key={index}
                  title={gauge.name}
                  data={{ value: gauge.value, max: gauge.max }}
                  type="gauge"
                  style={{ border: 'none', padding: '0' }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Performance Radar */}
        {charts.performanceRadar && charts.performanceRadar.indicators && charts.performanceRadar.data && (
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>Performance Radar by Location</h3>
            <ReactEChartsCore
              echarts={echarts}
              option={{
                title: { text: 'Performance Radar by Location', left: 'center' },
                tooltip: { trigger: 'item' },
                legend: {
                  data: charts.performanceRadar.data?.map((item: any) => item.name) || [],
                  top: 'bottom'
                },
                radar: {
                  indicator: charts.performanceRadar.indicators || []
                },
                series: [
                  {
                    name: 'Performance Metrics',
                    type: 'radar',
                    data: charts.performanceRadar.data || []
                  }
                ]
              }}
              style={{ height: '400px', width: '100%' }}
            />
          </div>
        )}

        {/* Conversion Funnel */}
        {charts.conversionFunnel && charts.conversionFunnel.data && (
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>Production Process Funnel</h3>
            <ReactEChartsCore
              echarts={echarts}
              option={{
                title: { text: 'Production Process Funnel', left: 'center' },
                tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c}' },
                series: [{
                  name: 'Funnel',
                  type: 'funnel',
                  left: '10%',
                  top: 60,
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
                  data: charts.conversionFunnel.data || []
                }]
              }}
              style={{ height: '400px', width: '100%' }}
            />
          </div>
        )}

        {/* Tree Hierarchy */}
        {charts.treeHierarchy && charts.treeHierarchy.data && (
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>Machine Hierarchy</h3>
            <ReactEChartsCore
              echarts={echarts}
              option={{
                title: { text: 'Machine Hierarchy', left: 'center' },
                tooltip: { trigger: 'item', triggerOn: 'mousemove' },
                series: [{
                  type: 'tree',
                  data: [charts.treeHierarchy.data],
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
                }]
              }}
              style={{ height: '400px', width: '100%' }}
            />
          </div>
        )}

        {/* Sankey Flow */}
        {charts.sankeyFlow && charts.sankeyFlow.nodes && charts.sankeyFlow.links && (
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>Process Flow</h3>
            <ReactEChartsCore
              echarts={echarts}
              option={{
                title: { text: 'Process Flow (Sankey)', left: 'center' },
                tooltip: { trigger: 'item', triggerOn: 'mousemove' },
                series: [{
                  type: 'sankey',
                  layout: 'none',
                  emphasis: {
                    focus: 'adjacency'
                  },
                  data: charts.sankeyFlow.nodes?.map((node: any) => ({
                    name: Array.isArray(node.name) ? node.name[0] : node.name
                  })) || [],
                  links: charts.sankeyFlow.links?.map((link: any) => ({
                    source: Array.isArray(link.source) ? link.source[0] : link.source,
                    target: Array.isArray(link.target) ? link.target[0] : link.target,
                    value: link.value
                  })) || []
                }]
              }}
              style={{ height: '400px', width: '100%' }}
            />
          </div>
        )}

        {/* Show error charts if they exist */}
        {charts.stackedArea && charts.stackedArea.error && (
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px', background: '#fff3cd' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '20px', color: '#856404' }}>Stacked Area Chart</h3>
            <div style={{ textAlign: 'center', color: '#856404' }}>
              Error: {charts.stackedArea.error}
            </div>
          </div>
        )}
      </div>

      {/* Debug Information */}
      <div style={{ marginTop: '40px', padding: '20px', background: '#f8f9fa', borderRadius: '8px' }}>
        <h3>Debug Information</h3>
        <details>
          <summary>Chart Data</summary>
          <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '300px' }}>
            {JSON.stringify(charts, null, 2)}
          </pre>
        </details>
        <details>
          <summary>Dashboard Data</summary>
          <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '300px' }}>
            {JSON.stringify(dashboardData, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );
}
