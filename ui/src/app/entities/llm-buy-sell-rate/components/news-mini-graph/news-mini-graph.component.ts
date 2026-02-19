import { Component, computed, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { subDays } from 'date-fns';
import { ApiService } from '../../../../shared/services/api.service';
import { InstrumentInList, NewsGraphItem } from '../../../../shared/types';
import { CandleInterval } from '../../../../shared/enums';
import { PreloaderComponent } from '../../../preloader/preloader.component';
import { EchartsGraphComponent } from '../../../echarts-graph/echarts-graph.component';
import { GRAPH_COLORS } from '../../../../shared/const';
import * as echarts from 'echarts';

const NEWS_GRAPH_DAYS = 20;

@Component({
  selector: 'news-mini-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [],
  templateUrl: './news-mini-graph.component.html',
  styleUrl: './news-mini-graph.component.scss'
})
export class NewsMiniGraphComponent {
  instrumentUid = input.required<InstrumentInList['uid']>();

  graphWidth = '50px';
  graphHeight = '50px';

  private _endDate = new Date();
  private _startDate = subDays(this._endDate, NEWS_GRAPH_DAYS);

  resource = resource<NewsGraphItem[], {uid: string, dateStart: Date, dateEnd: Date}>({
    request: () => ({
      uid: this.instrumentUid(),
      dateStart: this._startDate,
      dateEnd: this._endDate,
    }),
    loader: (params: ResourceLoaderParams<{uid: string, dateStart: Date, dateEnd: Date}>) => firstValueFrom(this._apiService.getInstrumentNewsGraph(
      params.request.uid,
      params.request.dateStart,
      params.request.dateEnd,
      CandleInterval.CANDLE_INTERVAL_DAY,
    )),
  });

  private _apiService = inject(ApiService);

  graphOptionsMini = computed<echarts.EChartsOption>(() => {
    const data = this.resource.value() ?? [];
    return this._getChartOptions(data);
  });

  private _getChartOptions(items: NewsGraphItem[]): echarts.EChartsOption {
    const values = items.map((p: any) => p.influence_score ?? 0);
    const dates = items.map((p: any) => new Date(p.date));

    if (values.length === 0) {
      return {};
    }

    const minValue = Math.min(...values, 0);
    const maxValue = Math.max(...values, 0);
    const padding = (maxValue - minValue) * 0.1 || 0.1;
    const yMin = minValue - padding;
    const yMax = maxValue + padding;

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
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 1,
            color: GRAPH_COLORS.news_influence_score
          },
          data: values,
          markLine: {
            silent: true,
            symbol: 'none',
            data: [
              { yAxis: 0, label: { show: false }, lineStyle: { color: '#999', width: 1.5, type: 'dashed' } },
            ]
          }
        }
      ]
    };
  }

}
