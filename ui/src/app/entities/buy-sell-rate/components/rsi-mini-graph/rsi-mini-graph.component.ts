import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import * as echarts from 'echarts';

@Component({
  selector: 'backtest-rsi-mini-graph',
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
export class BacktestRsiMiniGraphComponent {
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

  private _getChartOptions(rsiValues: number[]): echarts.EChartsOption {
    if (!rsiValues || rsiValues.length === 0) {
      return {};
    }

    // Генерируем индексы для X-оси (0, 1, 2, ...)
    const xData = rsiValues.map((_, i) => i);


    return <echarts.EChartsOption>{
      grid: { top: 0, right: 0, bottom: 0, left: 0 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: xData,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
        splitLine: { show: false },
      },
      series: [
        {
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 1 },
          itemStyle: { color: '#2196F3' },
          data: rsiValues,
          markLine: {
            silent: true,
            symbol: 'none',
            animation: false,
            data: [
              { yAxis: 30, label: { show: false }, lineStyle: { color: '#999', width: 0.5, type: 'dashed' } },
              { yAxis: 50, label: { show: false }, lineStyle: { color: '#999', width: 1.5, type: 'dashed' } },
              { yAxis: 70, label: { show: false }, lineStyle: { color: '#999', width: 0.5, type: 'dashed' } },
            ],
          },
        },
      ]
    };
  }
}
