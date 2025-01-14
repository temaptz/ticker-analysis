import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ApexAxisChartSeries,
  ApexChart,
  ApexTitleSubtitle,
  ApexXAxis,
  ApexYAxis,
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
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, PreloaderComponent],
  providers: [],
  templateUrl: './graph.component.html',
  styleUrl: './graph.component.scss'
})
export class GraphComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];
  @Input({required: true}) days!: number;
  @Input({required: true}) interval!: CandleInterval;

  isLoaded = signal<boolean>(false);
  series = signal<ApexAxisChartSeries | null>(null);
  chart?: ApexChart = {
    type: 'candlestick',
    width: 250,
    height: 150,
    toolbar: {
      show: false,
    },
    animations: {
      enabled: false,
    },
    zoom: {
      enabled: false,
    },
  };
  xaxis?: ApexXAxis = {
    type: 'datetime',
  };
  yaxis?: ApexYAxis = {
    tooltip: {
      enabled: true,
    },
  };
  title?: ApexTitleSubtitle;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentHistoryPrices(this.instrumentUid, this.days, this.interval)
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
  }

}
