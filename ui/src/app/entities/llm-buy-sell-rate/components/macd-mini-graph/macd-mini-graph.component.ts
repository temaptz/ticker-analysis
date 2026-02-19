import { Component, computed, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { subDays } from 'date-fns';
import { ApiService } from '../../../../shared/services/api.service';
import { InstrumentInList, TechAnalysisGraphItem } from '../../../../shared/types';
import { CandleInterval, IndicatorType } from '../../../../shared/enums';
import { PreloaderComponent } from '../../../preloader/preloader.component';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import * as echarts from 'echarts';


@Component({
  selector: 'macd-mini-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [],
  templateUrl: './macd-mini-graph.component.html',
  styleUrl: './macd-mini-graph.component.scss'
})
export class MacdMiniGraphComponent {
  instrumentUid = input.required<InstrumentInList['uid']>();
  graphWidth = input<string>('75px');
  graphHeight = input<string>('60px');

  private _endDate = new Date();
  private _startDateMini = subDays(this._endDate, 20);

  resource = resource<TechAnalysisGraphItem[], {uid: string, dateStartMini: Date, dateEnd: Date}>({
    request: () => ({
      uid: this.instrumentUid(),
      dateStartMini: this._startDateMini,
      dateEnd: this._endDate,
    }),
    loader: (params: ResourceLoaderParams<{uid: string, dateStartMini: Date, dateEnd: Date}>) => firstValueFrom(this._apiService.getInstrumentTechGraph(
      params.request.uid,
      IndicatorType.INDICATOR_TYPE_MACD,
      params.request.dateStartMini,
      params.request.dateEnd,
      CandleInterval.CANDLE_INTERVAL_DAY,
    )),
  });

  private _apiService = inject(ApiService);

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    return this._getChartOptions(this.resource.value() ?? []);
  });

  private _getChartOptions(graph: TechAnalysisGraphItem[]): echarts.EChartsOption {
    const limitedGraph = graph.slice(-7);
    const histValues = limitedGraph.map(i => (i?.macd ?? 0) - (i?.signal ?? 0));
    const absMax = histValues.length > 0
      ? Math.max(Math.abs(Math.min(...histValues)), Math.abs(Math.max(...histValues)))
      : 1;

    return <echarts.EChartsOption>{
      grid: { top: 0, right: 0, bottom: 0, left: 0 },
      xAxis: {
        type: 'category',
        data: limitedGraph.map(i => new Date(i.date)),
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
            itemStyle: { color: value >= 0 ? '#4caf50' : '#f44336' },
          })),
        },
      ],
    };
  }

}
