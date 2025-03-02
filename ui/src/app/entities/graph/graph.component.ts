import {
  AfterViewInit,
  Component,
  effect,
  ElementRef,
  input, OnDestroy,
  signal,
  ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { ApexAxisChartSeries, ApexOptions, ChartComponent, NgApexchartsModule } from 'ng-apexcharts';
import { parseJSON } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentHistoryPrice, InstrumentInList } from '../../types';
import { CandleInterval } from '../../enums';
import { getPriceByQuotation } from '../../utils';
import { debounce } from '../../shared/utils';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
  selector: 'graph',
  imports: [CommonModule, NgApexchartsModule, PreloaderComponent],
  providers: [],
  templateUrl: './graph.component.html',
  styleUrl: './graph.component.scss',
})
export class GraphComponent implements AfterViewInit, OnDestroy {

  instrumentUid = input.required<InstrumentInList['uid']>();
  days = input.required<number>();
  interval = input.required<CandleInterval>();
  width = input<string>('250px');
  height = input<string>('150px');

  isLoaded = signal<boolean>(false);
  series = signal<ApexAxisChartSeries | null>(null);
  graphOptions = signal<ApexOptions>({});

  private resizeObserver?: ResizeObserver;

  @ViewChild('chartComponent')
  private chartComponent?: ChartComponent;

  @ViewChild('container')
  private containerElRef?: ElementRef<HTMLDivElement>;

  constructor(
    private appService: ApiService,
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

  ngAfterViewInit(): void {
    setTimeout(() => {
      if (this.width() === '100%') {
        const container = this.containerElRef?.nativeElement;

        if (container) {
          // Инициализируем ResizeObserver и определяем колбэк-функцию
          this.resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
              if (entry.target === container) {
                this.redrawChart();
              }
            }
          });

          // Начинаем наблюдение за изменениями размера контейнера
          this.resizeObserver.observe(container);
        }
      }
    });
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
  }

  redrawChart= debounce(() => {
    this.chartComponent?.updateOptions(this.graphOptions());
  }, 300);

}
