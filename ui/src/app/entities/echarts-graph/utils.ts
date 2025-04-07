import * as echarts from 'echarts';

export const ECHARTS_MAIN_OPTIONS: echarts.EChartsOption = {
  grid: {
    top: 10,
    bottom: 10,
    left: 10,
    right: 10,
    containLabel: true,
  },
  xAxis: {
    type: 'time',
    axisLabel: {
      formatter: (value) => {
        const date = new Date(value);
        return new Intl.DateTimeFormat('ru-RU', {
          day: '2-digit',
          month: 'short',
          year: '2-digit'
        }).format(date);
      },
      rotate: 45,
    },
  },
  yAxis: {
    scale: true
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    },
  },
};
