import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import * as echarts from 'echarts';
import { parseJSON } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentHistoryPrice, InstrumentInList } from '../../shared/types';
import { CandleInterval } from '../../shared/enums';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';


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

  private apiService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.apiService.getInstrumentHistoryPrices(this.instrumentUid(), this.days(), this.interval())
        .pipe(
          finalize(() => this.isLoaded.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe((resp: InstrumentHistoryPrice[]) => this.initOption(resp));
    });
  }

  private initOption(history: InstrumentHistoryPrice[]): void {
    const option: echarts.EChartsOption = {
      ...ECHARTS_MAIN_OPTIONS,
      series: [
        {
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
