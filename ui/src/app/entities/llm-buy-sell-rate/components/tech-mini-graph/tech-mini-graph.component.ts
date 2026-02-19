import { Component, computed, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { addDays } from 'date-fns';
import { ApiService } from '../../../../shared/services/api.service';
import { InstrumentInList, PredictionGraphResp } from '../../../../shared/types';
import { CandleInterval, ModelNameEnum } from '../../../../shared/enums';
import { PreloaderComponent } from '../../../preloader/preloader.component';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import { GRAPH_COLORS } from '../../../../shared/const';
import * as echarts from 'echarts';

const TARGET_MAX_DAYS_COUNT = 20;

@Component({
  selector: 'tech-mini-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [],
  templateUrl: './tech-mini-graph.component.html',
  styleUrl: './tech-mini-graph.component.scss'
})
export class TechMiniGraphComponent {
  instrumentUid = input.required<InstrumentInList['uid']>();
  graphWidth = input<string>('75px');
  graphHeight = input<string>('60px');

  private _startDate = new Date();
  private _endDate = addDays(this._startDate, TARGET_MAX_DAYS_COUNT);

  resource = resource<PredictionGraphResp, {uid: string, dateStart: Date, dateEnd: Date}>({
    request: () => ({
      uid: this.instrumentUid(),
      dateStart: this._startDate,
      dateEnd: this._endDate,
    }),
    loader: (params: ResourceLoaderParams<{uid: string, dateStart: Date, dateEnd: Date}>) => firstValueFrom(this._apiService.getInstrumentPredictionGraph(
      params.request.uid,
      params.request.dateStart,
      params.request.dateEnd,
      CandleInterval.CANDLE_INTERVAL_DAY,
      [ModelNameEnum.Ta_3_tech]
    )),
  });

  private _apiService = inject(ApiService);

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    const data = this.resource.value();
    const predictions = data?.[ModelNameEnum.Ta_3_tech] ?? [];
    return this._getChartOptions(predictions);
  });

  private _getChartOptions(predictions: any[]): echarts.EChartsOption {
    const values = predictions.map((p: any) => p.prediction_percent);
    const dates = predictions.map((p: any) => new Date(p.date));
    
    if (values.length === 0) {
      return {};
    }
    
    const minValue = Math.min(...values, 0);
    const maxValue = Math.max(...values, 0);
    const padding = (maxValue - minValue) * 0.1 || 0.1;
    const yMin = minValue - padding;
    const yMax = maxValue + padding;

    const buyValues = values.map(v => (v > 0 ? v : null));
    const sellValues = values.map(v => (v <= 0 ? v : null));

    return <echarts.EChartsOption>{
      grid: { top: 2, right: 2, bottom: 2, left: 2 },
      xAxis: {
        type: 'category',
        data: dates,
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
