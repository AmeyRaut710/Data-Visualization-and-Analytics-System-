import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

export default function DynamicChart({ chartConfig, onFilter, isDark }) {
  const options = useMemo(() => {
    const { title, type, x_axis, y_axis, data } = chartConfig;
    
    // Base Option structure
    const base = {
        title: {
            text: title || '',
            left: 'center',
            textStyle: {
                fontSize: 14,
                fontWeight: 'bold',
                color: isDark ? '#e2e8f0' : '#334155'
            }
        },
        tooltip: { 
            trigger: type === 'pie' || type === 'donut' || type === 'treemap' ? 'item' : 'axis',
            backgroundColor: isDark ? 'rgba(30, 41, 59, 0.95)' : 'rgba(255, 255, 255, 0.95)',
            borderColor: isDark ? '#334155' : '#e2e8f0',
            textStyle: { color: isDark ? '#f8fafc' : '#1e293b' },
            extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border-radius: 8px;'
        },
        toolbox: {
            show: true,
            feature: {
                dataView: { readOnly: false, title: 'Data View', lang: ['Data View', 'Close', 'Refresh'] },
                saveAsImage: { title: 'Save Image' }
            }
        },
        grid: {
            left: '5%',
            right: '5%',
            bottom: '10%',
            containLabel: true
        },
        color: ['#118DFF', '#E66C37', '#6B007B', '#E044A7', '#1AAB40', '#D9B300', '#D64550', '#197278', '#12239E', '#744EC2'], // Vibrant Power BI style palette
        textStyle: { color: isDark ? '#cbd5e1' : '#64748b' }
    };

    if (type === 'pie') {
        return {
            ...base,
            legend: { top: 'bottom', textStyle: { color: isDark ? '#cbd5e1' : '#475569' } },
            series: [{
                type: 'pie',
                radius: '50%',
                data: data.map(d => ({ name: d[x_axis] || 'Unknown', value: d[y_axis] })),
                emphasis: {
                    itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
                }
            }]
        };
    }

    if (type === 'donut') {
        return {
            ...base,
            legend: { top: 'bottom', textStyle: { color: isDark ? '#cbd5e1' : '#475569' } },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: isDark ? '#1e293b' : '#fff',
                    borderWidth: 2
                },
                label: { show: false, position: 'center' },
                emphasis: {
                    label: { show: true, fontSize: 16, fontWeight: 'bold' }
                },
                labelLine: { show: false },
                data: data.map(d => ({ name: d[x_axis] || 'Unknown', value: d[y_axis] }))
            }]
        };
    }

    if (type === 'horizontal_bar') {
      return {
        ...base,
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: data.map(d => d[y_axis]), axisLabel: { width: 100, overflow: 'truncate' } },
        series: [
          {
            type: 'bar',
            data: data.map(d => d[x_axis]),
            itemStyle: { borderRadius: [0, 4, 4, 0] },
            colorBy: 'data'
          }
        ]
      };
    }

    if (type === 'bar') {
      return {
        ...base,
        xAxis: { type: 'category', data: data.map(d => d[x_axis]), axisLabel: { interval: 0, rotate: 30 } },
        yAxis: { type: 'value' },
        series: [
          {
            type: 'bar',
            data: data.map(d => d[y_axis]),
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            colorBy: 'data'
          }
        ]
      };
    }

    if (type === 'line') {
      return {
        ...base,
        xAxis: { type: 'category', data: data.map(d => d[x_axis]), boundaryGap: false },
        yAxis: { type: 'value' },
        series: [
          {
            type: 'line',
            data: data.map(d => d[y_axis]),
            smooth: true,
            areaStyle: {
              color: {
                type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [{ offset: 0, color: 'rgba(17, 141, 255, 0.5)' }, { offset: 1, color: 'rgba(17, 141, 255, 0.05)' }]
              }
            }
          }
        ],
        dataZoom: [{ type: 'inside' }, { type: 'slider' }]
      };
    }
    
    if (type === 'scatter') {
        return {
          ...base,
          xAxis: { type: 'value', name: x_axis },
          yAxis: { type: 'value', name: y_axis },
          series: [
            {
              type: 'scatter',
              data: data.map(d => [d[x_axis], d[y_axis]]),
              symbolSize: 8
            }
          ],
          dataZoom: [{ type: 'inside' }, { type: 'slider' }]
        };
    }

    if (type === 'histogram') {
    const values = data.map(d => d[x_axis]).filter(v => typeof v === 'number');
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bins = 15;
    const binSize = (max - min) / bins;
    const binCounts = Array(bins).fill(0);
    values.forEach(v => {
      const idx = Math.min(Math.floor((v - min) / binSize), bins - 1);
      if (idx >= 0 && !isNaN(idx)) binCounts[idx]++;
    });
    const xData = Array.from({length: bins}, (_, i) => `${(min + (i * binSize)).toFixed(1)} - ${(min + ((i+1) * binSize)).toFixed(1)}`);
    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xData, axisLabel: { rotate: 45, width: 60, overflow: 'truncate' } },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: binCounts, barWidth: '95%', itemStyle: { color: '#118DFF', borderRadius: [4, 4, 0, 0] } }]
    };
  }

  if (type === 'box') {
    const groups = {};
    data.forEach(d => {
      const c = d[x_axis];
      const v = d[y_axis];
      if (!groups[c]) groups[c] = [];
      if (typeof v === 'number') groups[c].push(v);
    });
    const categories = Object.keys(groups).slice(0, 15); // limit to 15 categories max
    const boxData = categories.map(c => {
      const sorted = groups[c].sort((a,b) => a-b);
      if(sorted.length === 0) return [0,0,0,0,0];
      const min = sorted[0];
      const max = sorted[sorted.length-1];
      const q1 = sorted[Math.floor(sorted.length * 0.25)];
      const median = sorted[Math.floor(sorted.length * 0.5)];
      const q3 = sorted[Math.floor(sorted.length * 0.75)];
      return [min, q1, median, q3, max];
    });
    
    return {
      tooltip: { trigger: 'item' },
      xAxis: { type: 'category', data: categories, axisLabel: { rotate: 45, width: 80, overflow: 'truncate' } },
      yAxis: { type: 'value' },
      series: [{ type: 'boxplot', data: boxData, itemStyle: { color: '#118DFF', borderColor: '#12239E' } }]
    };
  }

  if (type === 'treemap') {
        return {
            ...base,
            series: [{
                type: 'treemap',
                data: data.map(d => ({ name: String(d[x_axis]), value: d[y_axis] })),
                roam: false,
                nodeClick: false,
                breadcrumb: { show: false },
                itemStyle: { borderColor: isDark ? '#1e293b' : '#fff' }
            }]
        };
    }

    if (type === 'heatmap') {
        const xData = [...new Set(data.map(d => String(d[x_axis])))];
        const yData = [...new Set(data.map(d => String(d[y_axis])))];
        const heatData = data.map(d => [
            xData.indexOf(String(d[x_axis])),
            yData.indexOf(String(d[y_axis])),
            d[chartConfig.value_col] || 0
        ]);
        const vals = heatData.map(d => d[2]);
        const minVal = vals.length ? Math.min(...vals) : 0;
        const maxVal = vals.length ? Math.max(...vals) : 100;
        
        return {
            ...base,
            xAxis: { type: 'category', data: xData, axisLabel: { interval: 0, rotate: 30 } },
            yAxis: { type: 'category', data: yData },
            visualMap: {
                min: minVal,
                max: maxVal,
                calculable: true,
                orient: 'horizontal',
                left: 'center',
                bottom: '0%',
                inRange: { color: ['#F2F9FF', '#118DFF'] }, // Light to vibrant blue
                textStyle: { color: isDark ? '#cbd5e1' : '#64748b' }
            },
            series: [{
                type: 'heatmap',
                data: heatData,
                label: { show: true },
                itemStyle: { borderColor: isDark ? '#1e293b' : '#fff' }
            }]
        };
    }

    return base;
  }, [chartConfig, isDark]);

  const onEvents = {
    click: (params) => {
      if (onFilter && params.name) {
         // Pass the category clicked to the parent for cross-filtering
         onFilter(chartConfig.x_axis || chartConfig.y_axis, params.name);
      }
    }
  };

  if (chartConfig.type === 'matrix') {
    const { x_axis, y_axis, value_col, data } = chartConfig;
    // Pivot data
    const rows = [...new Set(data.map(d => String(d[x_axis])))];
    const cols = [...new Set(data.map(d => String(d[y_axis])))];
    
    const matrix = {};
    data.forEach(d => {
      const r = String(d[x_axis]);
      const c = String(d[y_axis]);
      if (!matrix[r]) matrix[r] = {};
      matrix[r][c] = d[value_col];
    });

    return (
      <div className={`h-full w-full overflow-auto p-4 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
        <h4 className="text-center font-bold mb-4">{chartConfig.title}</h4>
        <table className="w-full text-sm text-left">
          <thead className={isDark ? 'bg-slate-700' : 'bg-slate-50'}>
            <tr>
              <th className="p-2 border-b">{x_axis} \ {y_axis}</th>
              {cols.map(c => <th key={c} className="p-2 border-b">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r} className={`border-b ${isDark ? 'border-slate-700' : 'border-slate-100'}`}>
                <td className="p-2 font-medium">{r}</td>
                {cols.map(c => (
                  <td key={c} className="p-2">
                    {matrix[r]?.[c] ? new Intl.NumberFormat().format(matrix[r][c]) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className={`h-full w-full ${isDark ? '' : ''}`}>
      <ReactECharts 
        option={options} 
        style={{ height: '100%', width: '100%', minHeight: chartConfig.height || 300 }}
        onEvents={onEvents}
        notMerge={true}
      />
    </div>
  );
}
