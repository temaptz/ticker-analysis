import { Component, computed, inject, input, resource, ResourceLoaderParams, } from '@angular/core';
import { CommonModule } from '@angular/common';
import { combineLatest, firstValueFrom } from 'rxjs';
import { subDays } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, TechAnalysisResp } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { PreloaderComponent } from '../preloader/preloader.component';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import * as echarts from 'echarts';


@Component({
  selector: 'macd',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [],
  templateUrl: './macd.component.html',
  styleUrl: './macd.component.scss'
})
export class MacdComponent {
  instrumentUid = input.required<InstrumentInList['uid']>();

  graphHeight = '200px';

  private _endDate = new Date();
  private _startDateMini = subDays(this._endDate, 30);
  private _startDateLong = subDays(this._endDate, 30 * 12);

  resource = resource<TechAnalysisResp[], {uid: string, dateStartMini: Date, dateStartLong: Date, dateEnd: Date}>({
    request: () => ({
      uid: this.instrumentUid(),
      dateStartMini: this._startDateMini,
      dateStartLong: this._startDateLong,
      dateEnd: this._endDate,
    }),
    loader: (params: ResourceLoaderParams<{uid: string, dateStartMini: Date, dateStartLong: Date, dateEnd: Date}>) => firstValueFrom(combineLatest([
      this._apiService.getInstrumentTechGraph(
        params.request.uid,
        params.request.dateStartMini,
        params.request.dateEnd,
        CandleInterval.CANDLE_INTERVAL_DAY,
      ),
      this._apiService.getInstrumentTechGraph(
        params.request.uid,
        params.request.dateStartLong,
        params.request.dateEnd,
        CandleInterval.CANDLE_INTERVAL_WEEK,
      ),
    ])),
  });

  private _apiService = inject(ApiService);

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    return this._getChartOptions(this.resource.value()?.[0]?.MACD ?? []);
  });

  graphOptionsLong = computed<echarts.EChartsOption>(() => {
    return this._getChartOptions(this.resource.value()?.[1]?.MACD ?? []);
  });

  private _getChartOptions(graph: TechAnalysisResp['MACD']): echarts.EChartsOption {
    const values = graph.map(i => i?.macd ?? 0);
    const absMax = Math.max(Math.abs(Math.min(...values)), Math.abs(Math.max(...values)));

    return <echarts.EChartsOption>{
      grid: { top: 0, right: 0, bottom: 0, left: 0 },
      xAxis: {
        type: 'category',
        data: graph.map(i => new Date(i.date)),
        axisLabel: { show: false },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: -absMax,
        max: absMax,
        axisLabel: { show: false },
        splitLine: {
          show: false,
        },
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
            color: '#ff0000',
          },
          data: graph.map(i => i?.signal),
        },
        {
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 1,
          },
          itemStyle: {
            color: '#0000ff',
          },
          data: graph.map(i => i?.macd),
        },
        {
          type: 'bar',
          barWidth: '90%',
          data: graph.map(i => {
            const value = (i?.macd ?? 0) - (i?.signal ?? 0);
            const color = (value >= 0) ? '#00ff00' : '#ff0000';

            return {
              value,
              itemStyle: {
                color,
              }
            };
          }),
        },
      ]
    };
  }

}
