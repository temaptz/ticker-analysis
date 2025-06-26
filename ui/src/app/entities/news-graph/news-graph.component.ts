import {
  input,
  inject,
  resource,
  Component,
  numberAttribute,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom, map } from 'rxjs';
import { endOfDay, parseJSON, startOfDay, subDays } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { GRAPH_COLORS } from '../../shared/const';
import { InstrumentInList, NewsGraphItem } from '../../shared/types';
import { getRoundPrice } from '../../utils';
import { CandleInterval } from '../../shared/enums';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';

interface NewsGraphParams {
  uid: string;
  interval: CandleInterval;
  historyDaysCount: number;
}


@Component({
  selector: 'news-graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [PriceFormatPipe],
  templateUrl: './news-graph.component.html',
  styleUrl: './news-graph.component.scss'
})
export class NewsGraphComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  interval = input<CandleInterval>(CandleInterval.CANDLE_INTERVAL_WEEK);
  historyDaysCount = input(90, { transform: numberAttribute });
  futureDaysCount = input(90, { transform: numberAttribute });
  width = input<string>('450px');
  height = input<string>('150px');

  private readonly apiService = inject(ApiService);

  option = resource<echarts.EChartsOption | null, NewsGraphParams>({
    request: () => ({
      uid: this.instrumentUid(),
      interval: this.interval(),
      historyDaysCount: this.historyDaysCount(),
    }),
    loader: (params) => firstValueFrom(
      this.apiService.getInstrumentNewsGraph(
        params.request.uid,
        startOfDay(subDays(new Date(), params.request.historyDaysCount)),
        endOfDay(new Date()),
        params.request.interval,
      )
        .pipe(
          map((resp: NewsGraphItem[]): echarts.EChartsOption | null => ({
            ...ECHARTS_MAIN_OPTIONS,
            series: {
              name: 'Influence Score',
              type: 'line',
              showSymbol: true,
              symbol: 'circle',
              symbolSize: 2.5,
              itemStyle: {
                color: GRAPH_COLORS.influence_score
              },
              lineStyle: {
                width: 1,
              },
              encode: {
                x: 0,
                y: 1,
              },
              data: resp?.map(i => [
                  parseJSON(i.date),
                  getRoundPrice(i.influence_score),
                ]
              ) ?? []
            },
          })),
        )
    ),
  })

}

