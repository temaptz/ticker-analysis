import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ApexAxisChartSeries,
  ApexOptions,
  NgApexchartsModule
} from 'ng-apexcharts';
import { AppService } from '../../app.service';
import { InstrumentHistoryPrice, InstrumentInList } from '../../types';
import { CandleInterval } from '../../enums';
import { parseJSON } from 'date-fns';
import { getPriceByQuotation } from '../../utils';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
    selector: 'graph',
    imports: [CommonModule, NgApexchartsModule, PreloaderComponent],
    providers: [],
    templateUrl: './graph.component.html',
    styleUrl: './graph.component.scss'
})
export class GraphComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  days = input.required<number>();
  interval = input.required<CandleInterval>();
  width = input<string>('250px');
  height = input<string>('150px');

  isLoaded = signal<boolean>(false);
  series = signal<ApexAxisChartSeries | null>(null);
  graphOptions = signal<ApexOptions>({});

  constructor(
    private appService: AppService,
  ) {
    effect(() => {
      const nextOptions: ApexOptions = {
        chart: {
          type: 'candlestick',
          width: this.width(),
          height: this.height(),
          toolbar: {
            show: false,
          },
          animations: {
            enabled: false,
          },
          zoom: {
            enabled: false,
          },
        },
        xaxis: {
          type: 'datetime',
        },
        yaxis: {
          tooltip: {
            enabled: true,
          },
        },
      }

      this.graphOptions.set(nextOptions)
    });

    effect(() => {
      this.appService.getInstrumentHistoryPrices(this.instrumentUid(), this.days(), this.interval())
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe((resp: InstrumentHistoryPrice[]) => {
          const series: ApexAxisChartSeries = [{
            data: resp?.map(i => [
                parseJSON(i.time).getTime(),
                getPriceByQuotation(i.open) ?? 0,
                getPriceByQuotation(i.high) ?? 0,
                getPriceByQuotation(i.low) ?? 0,
                getPriceByQuotation(i.close) ?? 0,
              ])
              ?? [],
          }];
          this.series.set(series);
        });
    });
  }

}
