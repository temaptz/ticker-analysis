import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ApexAxisChartSeries,
  ApexChart, ApexDataLabels,
  ApexTitleSubtitle, ApexTooltip,
  ApexXAxis,
  ApexYAxis,
  NgApexchartsModule,
  ApexOptions
} from 'ng-apexcharts';
import { AppService } from '../../app.service';
import { InstrumentHistoryPrice, InstrumentInList, PredictionGraph } from '../../types';
import { addDays, parseJSON } from 'date-fns';
import { combineLatest, finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { getPriceByQuotation, getRoundPrice } from '../../utils';
import { CandleInterval } from '../../enums';


@Component({
  selector: 'complex-graph',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, PreloaderComponent],
  providers: [],
  templateUrl: './complex-graph.component.html',
  styleUrl: './complex-graph.component.scss'
})
export class ComplexGraphComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  isLoaded = signal<boolean>(false);
  series = signal<ApexAxisChartSeries | null>(null);

  chartOptions: ApexOptions = {
    chart: {
      type: 'line',
      width: 450,
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
    },
    xaxis: {
      type: 'datetime',
    },
    legend: {
      show: false,
    },
  }

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    combineLatest([
      this.appService.getInstrumentHistoryPrices(
        this.instrumentUid,
        30,
        CandleInterval.CANDLE_INTERVAL_DAY
      ),
      this.appService.getInstrumentPredictionGraph(this.instrumentUid)
    ])
      .pipe(
        finalize(() => this.isLoaded.set(true))
      )
      .subscribe((resp: [InstrumentHistoryPrice[], PredictionGraph[]]) => {
        const respHistory = resp[0];
        const respPredictions = resp[1];

        const series = [
          {
            name: 'Фактически',
            type: 'candlestick',
            data: resp?.[0]?.map(i => ({
              x: parseJSON(i.time),
              y: [
                getPriceByQuotation(i.open) ?? 0,
                getPriceByQuotation(i.high) ?? 0,
                getPriceByQuotation(i.low) ?? 0,
                getPriceByQuotation(i.close) ?? 0
              ],
            })) ?? [],
          },
          {
            name: 'Предсказания',
            type: 'line',
            data: resp?.[1]?.map(i => ({
                y: getRoundPrice(i.prediction),
                x: addDays(parseJSON(i.date), 30),
              }))
              ?? [],
          }
        ];

        this.series.set(series);
      });
  }

}
