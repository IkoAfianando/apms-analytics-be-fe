import { useState, useEffect } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import {
  LineChart,
  BarChart,
  PieChart,
  GaugeChart
} from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  VisualMapComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { getJSON } from '../lib/api';

// Register the required components
echarts.use([
  LineChart,
  BarChart,
  PieChart,
  GaugeChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  VisualMapComponent,
  CanvasRenderer
]);

interface DashboardData {
  production: {
    totalProduced: number;
    totalLogs: number;
    efficiency: number;
    uniqueLocations: number;
  };
  machines: {
    total: number;
    locations: number;
  };
  summary: {
    status: string;
    dataPoints: number;
    productionRate: number;
  };
}

interface ChartData {
  xAxis?: string[];
  series?: any[];
  data?: any[];
  [key: string]: any;
}

const ChartComponent = ({ title, data, type = 'line', height = 400 }: {
  title: string;
  data: ChartData;
  type?: string;
  height?: number;
}) => {
  const getOption = () => {
    const baseOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: type === 'pie' ? 'item' : 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: '#ccc',
        borderWidth: 1
      },
      legend: {
        top: 'bottom',
        textStyle: {
          fontSize: 12
        }
      }
    };

    switch (type) {
      case 'line':
        return {
          ...baseOption,
          grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: data.xAxis || [],
            axisLabel: {
              fontSize: 11,
              rotate: 45
            }
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              fontSize: 11
            }
          },
          series: (data.series || []).map((s: any) => ({
            ...s,
            smooth: true,
            lineStyle: {
              width: 3
            },
            symbolSize: 6
          }))
        };

      case 'bar':
        return {
          ...baseOption,
          grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: data.xAxis || [],
            axisLabel: {
              fontSize: 11,
              rotate: 45
            }
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              fontSize: 11
            }
          },
          series: (data.series || []).map((s: any) => ({
            ...s,
            itemStyle: {
              borderRadius: [4, 4, 0, 0]
            }
          }))
        };

      case 'pie':
        return {
          ...baseOption,
          series: [
            {
              name: title,
              type: 'pie',
              radius: ['40%', '70%'],
              center: ['50%', '50%'],
              data: data.data || [],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              },
              label: {
                fontSize: 11
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
              center: ['50%', '60%'],
              startAngle: 200,
              endAngle: -20,
              min: 0,
              max: data.max || 100,
              splitNumber: 10,
              itemStyle: {
                color: '#58D9F9',
                shadowColor: 'rgba(0,138,255,0.45)',
                shadowBlur: 10,
                shadowOffsetX: 2,
                shadowOffsetY: 2
              },
              progress: {
                show: true,
                roundCap: true,
                width: 18
              },
              pointer: {
                icon: 'path://M2090.36389,615.30999 L2090.36389,615.30999 C2091.48372,615.30999 2092.40383,616.194028 2092.44859,617.312956 L2096.90698,728.755929 C2097.05155,732.369577 2094.2393,735.416212 2090.62566,735.56078 C2090.53845,735.564269 2090.45117,735.566014 2090.36389,735.566014 L2090.36389,735.566014 C2086.74736,735.566014 2083.81557,732.63423 2083.81557,729.017692 C2083.81557,728.930412 2083.81732,728.84314 2083.82081,728.755929 L2088.2792,617.312956 C2088.32396,616.194028 2089.24407,615.30999 2090.36389,615.30999 Z',
                length: '75%',
                width: 16,
                offsetCenter: [0, '5%']
              },
              axisLine: {
                roundCap: true,
                lineStyle: {
                  width: 18
                }
              },
              axisTick: {
                splitNumber: 2,
                lineStyle: {
                  width: 2,
                  color: '#999'
                }
              },
              splitLine: {
                length: 12,
                lineStyle: {
                  width: 3,
                  color: '#999'
                }
              },
              axisLabel: {
                distance: 30,
                color: '#999',
                fontSize: 20
              },
              title: {
                show: false
              },
              detail: {
                backgroundColor: '#fff',
                borderColor: '#999',
                borderWidth: 2,
                width: '60%',
                lineHeight: 40,
                height: 40,
                borderRadius: 8,
                offsetCenter: [0, '35%'],
                valueAnimation: true,
                formatter: function (value: number) {
                  return '{value|' + value.toFixed(1) + '}{unit|%}';
                },
                rich: {
                  value: {
                    fontSize: 50,
                    fontWeight: 'bolder',
                    color: '#777'
                  },
                  unit: {
                    fontSize: 20,
                    color: '#999',
                    padding: [0, 0, -20, 10]
                  }
                }
              },
              data: [{ value: data.value || 0, name: title }]
            }
          ]
        };

      default:
        return baseOption;
    }
  };

  return (
    <div style={{ 
      border: '1px solid #e0e0e0', 
      borderRadius: '12px', 
      padding: '16px', 
      backgroundColor: '#fff',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <ReactEChartsCore
        echarts={echarts}
        option={getOption()}
        style={{ height: `${height}px`, width: '100%' }}
      />
    </div>
  );
};

export default function WorkingDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [charts, setCharts] = useState<{ [key: string]: ChartData }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log('Testing API connection...');
        const healthCheck = await getJSON<{ ok: boolean }>('/health');
        console.log('Health check result:', healthCheck);

        if (!healthCheck.ok) {
          throw new Error('API health check failed');
        }

        // Load dashboard overview
        console.log('Loading dashboard overview...');
        const overview = await getJSON<DashboardData>('/simple-dashboard/overview');
        console.log('Dashboard overview:', overview);
        setDashboardData(overview);

        // Load chart data in parallel
        const chartPromises = [
          getJSON<ChartData>('/simple-timerlogs/pie-chart').then(data => ({ type: 'stopReasonsPie', data })),
          getJSON<ChartData>('/simple-timerlogs/bar-chart').then(data => ({ type: 'locationBar', data })),
          getJSON<ChartData>('/simple-timerlogs/line-chart').then(data => ({ type: 'dailyTrend', data })),
          getJSON<any>('/simple-dashboard/recent-activity').then(data => ({ type: 'recentActivity', data })),
          getJSON<any>('/simple-dashboard/machine-status').then(data => ({ type: 'machineStatus', data }))
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
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '18px', marginBottom: '10px' }}>Loading Dashboard...</div>
          <div style={{ fontSize: '14px', color: '#666' }}>Fetching data from APMS Analytics API</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh', 
        flexDirection: 'column',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{ 
          background: 'white', 
          padding: '30px', 
          borderRadius: '12px', 
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h2 style={{ color: '#dc3545', marginBottom: '15px' }}>Error Loading Dashboard</h2>
          <p style={{ marginBottom: '20px', color: '#666' }}>{error}</p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f5f5f5',
      minHeight: '100vh'
    }}>
      <h1 style={{ 
        textAlign: 'center', 
        marginBottom: '30px',
        color: '#333',
        fontSize: '28px',
        fontWeight: '300'
      }}>
        🎯 APMS Analytics Dashboard
      </h1>

      {/* KPI Cards */}
      {dashboardData && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '20px', 
          marginBottom: '30px' 
        }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #007bff, #0056b3)', 
            color: 'white',
            padding: '25px', 
            borderRadius: '12px', 
            textAlign: 'center',
            boxShadow: '0 4px 12px rgba(0,123,255,0.3)'
          }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', opacity: 0.9 }}>Total Production</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', margin: '10px 0' }}>
              {dashboardData.production.totalProduced.toLocaleString()}
            </div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>Units Produced</div>
            <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.9 }}>
              Efficiency: {dashboardData.production.efficiency}%
            </div>
          </div>

          <div style={{ 
            background: 'linear-gradient(135deg, #28a745, #1e7e34)', 
            color: 'white',
            padding: '25px', 
            borderRadius: '12px', 
            textAlign: 'center',
            boxShadow: '0 4px 12px rgba(40,167,69,0.3)'
          }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', opacity: 0.9 }}>System Status</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', margin: '10px 0' }}>
              {dashboardData.summary.status.toUpperCase()}
            </div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>Overall System</div>
            <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.9 }}>
              Rate: {dashboardData.summary.productionRate}%
            </div>
          </div>

          <div style={{ 
            background: 'linear-gradient(135deg, #17a2b8, #117a8b)', 
            color: 'white',
            padding: '25px', 
            borderRadius: '12px', 
            textAlign: 'center',
            boxShadow: '0 4px 12px rgba(23,162,184,0.3)'
          }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', opacity: 0.9 }}>Machines</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', margin: '10px 0' }}>
              {dashboardData.machines.total}
            </div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>Total Machines</div>
            <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.9 }}>
              Locations: {dashboardData.machines.locations}
            </div>
          </div>

          <div style={{ 
            background: 'linear-gradient(135deg, #ffc107, #e0a800)', 
            color: '#333',
            padding: '25px', 
            borderRadius: '12px', 
            textAlign: 'center',
            boxShadow: '0 4px 12px rgba(255,193,7,0.3)'
          }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', opacity: 0.9 }}>Data Points</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', margin: '10px 0' }}>
              {dashboardData.summary.dataPoints.toLocaleString()}
            </div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>Total Records</div>
            <div style={{ fontSize: '14px', marginTop: '10px', opacity: 0.9 }}>
              All Collections
            </div>
          </div>
        </div>
      )}

      {/* Efficiency Gauge */}
      {dashboardData && (
        <div style={{ marginBottom: '30px' }}>
          <ChartComponent
            title="Production Efficiency"
            data={{
              value: dashboardData.production.efficiency,
              max: 100
            }}
            type="gauge"
            height={300}
          />
        </div>
      )}

      {/* Charts Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', 
        gap: '20px' 
      }}>
        
        {/* Stop Reasons Pie Chart */}
        {charts.stopReasonsPie && (
          <ChartComponent
            title="Stop Reason Distribution"
            data={charts.stopReasonsPie}
            type="pie"
            height={400}
          />
        )}

        {/* Location Bar Chart */}
        {charts.locationBar && (
          <ChartComponent
            title="Timer Logs by Location"
            data={charts.locationBar}
            type="bar"
            height={400}
          />
        )}

        {/* Daily Trend Line Chart */}
        {charts.dailyTrend && (
          <ChartComponent
            title="Daily Activity Trend (Last 30 Days)"
            data={charts.dailyTrend}
            type="line"
            height={400}
          />
        )}

        {/* Recent Activity */}
        {charts.recentActivity && charts.recentActivity.hourlyData && (
          <ChartComponent
            title="Recent Hourly Activity (Last 24h)"
            data={{
              xAxis: charts.recentActivity.hourlyData.hours,
              series: [
                {
                  name: "Total Events",
                  type: "bar",
                  data: charts.recentActivity.hourlyData.total
                },
                {
                  name: "Production Units",
                  type: "line",
                  data: charts.recentActivity.hourlyData.production
                }
              ]
            }}
            type="bar"
            height={400}
          />
        )}

        {/* Machine Status Distribution */}
        {charts.machineStatus && charts.machineStatus.statusDistribution && (
          <ChartComponent
            title="Machine Status Distribution"
            data={charts.machineStatus.statusDistribution}
            type="pie"
            height={400}
          />
        )}

        {/* Machine Location Distribution */}
        {charts.machineStatus && charts.machineStatus.locationDistribution && (
          <ChartComponent
            title="Machines by Location"
            data={{
              xAxis: charts.machineStatus.locationDistribution.map((item: any) => item.name),
              series: [
                {
                  name: "Machine Count",
                  type: "bar",
                  data: charts.machineStatus.locationDistribution.map((item: any) => item.value)
                }
              ]
            }}
            type="bar"
            height={400}
          />
        )}
      </div>

      {/* Footer with stats */}
      <div style={{ 
        marginTop: '40px', 
        padding: '20px', 
        background: 'white', 
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        textAlign: 'center',
        color: '#666'
      }}>
        <h3 style={{ marginBottom: '15px', color: '#333' }}>Dashboard Information</h3>
        <p>Real-time data from APMS (Advanced Production Management System)</p>
        <p>
          {dashboardData && (
            <>
              Showing data from {dashboardData.machines.locations} locations with {dashboardData.machines.total} machines
              <br />
              Total data points: {dashboardData.summary.dataPoints.toLocaleString()} records
            </>
          )}
        </p>
      </div>
    </div>
  );
}
