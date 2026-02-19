import { Component, computed, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom, startWith } from 'rxjs';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { ApiService } from '../../../../shared/services/api.service';
import { InstrumentInList, TechAnalysisResp } from '../../../../shared/types';
import { CandleInterval } from '../../../../shared/enums';
import { PreloaderComponent } from '../../../preloader/preloader.component';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import * as echarts from 'echarts';


@Component({
  selector: 'rsi-mini-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [],
  templateUrl: './rsi-mini-graph.component.html',
  styleUrl: './rsi-mini-graph.component.scss'
})
export class RsiMiniGraphComponent {
  instrumentUid = input.required<InstrumentInList['uid']>();
  graphWidth = input<string>('75px');
  graphHeight = input<string>('60px');

  private static readonly RSI_CANDLES_COUNT = 7;

  private _endDate = new Date();

  resource = resource<TechAnalysisResp, {uid: string, dateStartMini: Date, dateEnd: Date}>({
    request: () => ({
      uid: this.instrumentUid(),
      dateStartMini: subDays(startOfDay(this._endDate), RsiMiniGraphComponent.RSI_CANDLES_COUNT),
      dateEnd: endOfDay(this._endDate),
    }),
    loader: (params: ResourceLoaderParams<{uid: string, dateStartMini: Date, dateEnd: Date}>) => firstValueFrom(this._apiService.getInstrumentTechGraph(
      params.request.uid,
      params.request.dateStartMini,
      params.request.dateEnd,
      CandleInterval.CANDLE_INTERVAL_DAY,
      14,
    )),
  });

  private _apiService = inject(ApiService);

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    return this._getChartOptions(this.resource.value()?.RSI ?? []);
  });

  private _getChartOptions(graph: TechAnalysisResp['RSI']): echarts.EChartsOption {
    const limitedGraph = graph.slice(-RsiMiniGraphComponent.RSI_CANDLES_COUNT);
    const values = limitedGraph.map(i => i?.signal ?? 0);

    return <echarts.EChartsOption>{
      grid: { top: 0, right: 0, bottom: 0, left: 0 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: limitedGraph.map(i => new Date(i.date)),
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
          data: values,
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
