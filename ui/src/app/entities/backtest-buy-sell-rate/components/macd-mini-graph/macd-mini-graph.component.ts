import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import * as echarts from 'echarts';
import { GRAPH_COLORS } from '../../../../shared/const';

@Component({
  selector: 'backtest-macd-mini-graph',
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
export class BacktestMacdMiniGraphComponent {
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

  private _getChartOptions(histValues: number[]): echarts.EChartsOption {
    if (!histValues || histValues.length === 0) {
      return {};
    }

    const absMax = histValues.length > 0
      ? Math.max(Math.abs(Math.min(...histValues)), Math.abs(Math.max(...histValues)))
      : 1;

    // Генерируем индексы для X-оси (0, 1, 2, ...)
    const xData = histValues.map((_, i) => i);

    return <echarts.EChartsOption>{
      grid: { top: 0, right: 0, bottom: 0, left: 0 },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: -absMax,
        max: absMax,
        axisLabel: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
        splitLine: { show: false },
      },
      series: [
        {
          type: 'bar',
          barWidth: '90%',
          data: histValues.map(value => ({
            value,
            itemStyle: { color: value >= 0 ? GRAPH_COLORS.buy : GRAPH_COLORS.sell },
          })),
        },
      ],
    };
  }
}
