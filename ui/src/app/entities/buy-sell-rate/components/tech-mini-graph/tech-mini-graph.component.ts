import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import { GRAPH_COLORS } from '../../../../shared/const';
import * as echarts from 'echarts';

@Component({
  selector: 'backtest-tech-mini-graph',
  imports: [CommonModule, EchartsGraphComponent],
  providers: [],
  template: `
    <div class="mini-graph-wrapper" [style.width]="graphWidth()" [style.height]="graphHeight()">
      @if (hasData()) {
        <echarts-graph [width]="graphWidth()" [height]="graphHeight()" [option]="graphOptionsMini()"/>
      }
    </div>
  `,
  styles: [`
    .mini-graph-wrapper {
      border: 1px solid lightgray;
    }
  `]
})
export class BacktestTechMiniGraphComponent {
  graphData = input<number[] | null | undefined>(null);
  graphWidth = input<string>('75px');
  graphHeight = input<string>('60px');

  hasData = computed(() => {
    const data = this.graphData();
    return data !== null && data !== undefined && data.length > 0;
  });

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    return this._getChartOptions(this.graphData() ?? []);
  });

  private _getChartOptions(predictionValues: number[]): echarts.EChartsOption {
    if (!predictionValues || predictionValues.length === 0) {
      return {};
    }

    // Фильтруем null значения для расчета min/max
    const validValues = predictionValues.filter(v => v !== null && v !== undefined);
    
    if (validValues.length === 0) {
      return {};
    }

    const minValue = Math.min(...validValues, 0);
    const maxValue = Math.max(...validValues, 0);
    const padding = (maxValue - minValue) * 0.1 || 0.1;
    const yMin = minValue - padding;
    const yMax = maxValue + padding;

    // Разделяем значения на положительные (buy) и отрицательные (sell)
    const buyValues = predictionValues.map(v => (v !== null && v !== undefined && v > 0 ? v : null));
    const sellValues = predictionValues.map(v => (v !== null && v !== undefined && v <= 0 ? v : null));

    // Генерируем индексы для X-оси
    const xData = predictionValues.map((_, i) => i);

    return <echarts.EChartsOption>{
      grid: { top: 2, right: 2, bottom: 2, left: 2 },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: yMin,
        max: yMax,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
        splitLine: { show: false },
      },
      series: [
        {
          type: 'line',
          smooth: false,
          showSymbol: false,
          connectNulls: false,
          lineStyle: { width: 1, color: GRAPH_COLORS.buy },
          itemStyle: { color: GRAPH_COLORS.buy },
          data: buyValues,
          markLine: {
            silent: true,
            symbol: 'none',
            animation: false,
            data: [
              { yAxis: 0, label: { show: false }, lineStyle: { color: '#999', width: 1.5, type: 'dashed' } },
            ],
          }
        },
        {
          type: 'line',
          smooth: false,
          showSymbol: false,
          connectNulls: false,
          lineStyle: { width: 1, color: GRAPH_COLORS.sell },
          itemStyle: { color: GRAPH_COLORS.sell },
          data: sellValues,
        },
      ]
    };
  }
}
