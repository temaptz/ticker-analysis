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
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, PredictionGraph } from '../../types';
import { addDays, parseJSON } from 'date-fns';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { getRoundPrice } from '../../utils';


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
    this.appService.getInstrumentPredictionGraph(this.instrumentUid)
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: PredictionGraph[]) => {
        const series: ApexAxisChartSeries = [{
          data: resp?.map(i => ({
              y: getRoundPrice(i.prediction),
              x: addDays(parseJSON(i.date), 30),
            }))
            ?? [],
        }];
        this.series.set(series);
      });
  }

}
