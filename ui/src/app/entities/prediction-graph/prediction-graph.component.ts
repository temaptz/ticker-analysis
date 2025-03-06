import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApexAxisChartSeries, ApexOptions, NgApexchartsModule } from 'ng-apexcharts';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, PredictionGraph, PredictionResp } from '../../types';
import { addDays, endOfDay, parseJSON, startOfDay, subDays } from 'date-fns';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { getRoundPrice } from '../../utils';
import { CandleInterval } from '../../enums';


@Component({
  selector: 'prediction-graph',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, PreloaderComponent],
  providers: [],
  templateUrl: './prediction-graph.component.html',
  styleUrl: './prediction-graph.component.scss'
})
export class PredictionGraphComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  isLoaded = signal<boolean>(false);
  series = signal<ApexAxisChartSeries | null>(null);

  chartOptions: ApexOptions = {
    chart: {
      type: 'line',
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
    },
    xaxis: {
      type: 'datetime',
      tooltip: {
        enabled: false,
      },
    },
    yaxis: {
      tooltip: {
        enabled: false,
      },
    },
    tooltip: {
      marker: {
        show: false,
      },
      x: {
        show: true,
        format: 'dd MMM',
        formatter: undefined,
      },
      y: {
        formatter: undefined,
        title: {
          formatter: () => '',
        },
      },
    },
  }

  constructor(
    private appService: ApiService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentPredictionGraph(
      this.instrumentUid,
      startOfDay(subDays(new Date(), 30)),
      endOfDay(addDays(new Date(), 30)),
      CandleInterval.CANDLE_INTERVAL_DAY,
    )
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: PredictionResp) => {
        const series: ApexAxisChartSeries = [{
          data: resp?.ta1?.map(i => ({
              y: getRoundPrice(i.prediction),
              x: addDays(parseJSON(i.date), 30),
            }))
            ?? [],
        }];
        this.series.set(series);
      });
  }

}
