import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import * as echarts from 'echarts';
import { parseJSON } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentHistoryPrice, InstrumentInList } from '../../types';
import { CandleInterval } from '../../enums';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';


@Component({
  selector: 'graph',
  imports: [CommonModule, PreloaderComponent, EchartsGraphComponent],
  providers: [],
  templateUrl: './graph.component.html',
  styleUrl: './graph.component.scss',
})
export class GraphComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  days = input.required<number>();
  interval = input.required<CandleInterval>();
  width = input<string>('250px');
  height = input<string>('150px');

  isLoaded = signal<boolean>(false);
  option = signal<echarts.EChartsOption>({});

  constructor(
    private appService: ApiService,
  ) {
    effect(() => {
      this.appService.getInstrumentHistoryPrices(this.instrumentUid(), this.days(), this.interval())
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe((resp: InstrumentHistoryPrice[]) => this.initOption(resp));
    });
  }

  private initOption(history: InstrumentHistoryPrice[]): void {
    const option: echarts.EChartsOption = {
      grid: {
        top: 10,
        bottom: 10,
        left: 10,
        right: 10,
        containLabel: true,
      },
      xAxis: {
        type: 'time',
        axisLabel: {
          formatter: function (value) {
            const date = new Date(value);
            return new Intl.DateTimeFormat('ru-RU', {
              day: '2-digit',
              month: 'short',
              year: '2-digit'
            }).format(date);
          }
        }
      },
      yAxis: {
        scale: true
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
      },
      series: [
        {
          name: 'Фактически',
          type: 'candlestick',
          barWidth: 1.5,
          itemStyle: {
            color: '#00b050',
            color0: '#ff0000',
            borderColor: '#00b050',
            borderColor0: '#ff0000',
          },
          encode: {
            x: 0,
            y: [1, 2, 3, 4]
          },
          data: history?.map(i => [
            parseJSON(i.time),                 // x
            getPriceByQuotation(i.open) ?? 0,  // open
            getPriceByQuotation(i.close) ?? 0, // close
            getPriceByQuotation(i.low) ?? 0,   // low
            getPriceByQuotation(i.high) ?? 0   // high
          ]) ?? [],
        }
      ]
    };

    this.option.set(option);
  }

}
