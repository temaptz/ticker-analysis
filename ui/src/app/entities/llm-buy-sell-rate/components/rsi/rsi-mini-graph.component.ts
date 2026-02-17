import { Component, computed, inject, input, resource, ResourceLoaderParams, } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { subDays } from 'date-fns';
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

  graphWidth = '50px';
  graphHeight = '50px';

  private _endDate = new Date();
  private _startDateMini = subDays(this._endDate, 20);

  resource = resource<TechAnalysisResp, {uid: string, dateStartMini: Date, dateEnd: Date}>({
    request: () => ({
      uid: this.instrumentUid(),
      dateStartMini: this._startDateMini,
      dateEnd: this._endDate,
    }),
    loader: (params: ResourceLoaderParams<{uid: string, dateStartMini: Date, dateEnd: Date}>) => firstValueFrom(this._apiService.getInstrumentTechGraph(
      params.request.uid,
      params.request.dateStartMini,
      params.request.dateEnd,
      CandleInterval.CANDLE_INTERVAL_DAY,
    )),
  });

  private _apiService = inject(ApiService);

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    return this._getChartOptions(this.resource.value()?.RSI ?? []);
  });

  private _getChartOptions(graph: TechAnalysisResp['RSI']): echarts.EChartsOption {
    const limitedGraph = graph.slice(-7);
    const values = limitedGraph.map(i => i?.signal ?? 0);

    return <echarts.EChartsOption>{
      grid: { top: 2, right: 2, bottom: 2, left: 2 },
      xAxis: {
        type: 'category',
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
        splitLine: {
          show: true,
          lineStyle: {
            color: '#e0e0e0',
            width: 0.5,
            type: 'solid'
          }
        },
        splitNumber: 4,
      },
      series: [
        {
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 1,
          },
          itemStyle: {
            color: '#2196F3',
          },
          data: values,
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: {
              color: '#999',
              width: 1,
              type: 'dashed'
            },
            data: [
              { yAxis: 30, label: { show: false } },
              { yAxis: 50, label: { show: false } },
              { yAxis: 70, label: { show: false } }
            ]
          }
        }
      ]
    };
  }

}
