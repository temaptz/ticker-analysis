import {
  Component, computed, DestroyRef,
  effect, inject,
  input, model,
  numberAttribute, output,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { map, Observable, of, switchMap, tap } from 'rxjs';
import { addDays, endOfDay, isAfter, parseJSON, startOfDay, subDays } from 'date-fns';
import * as echarts from 'echarts';
import { ApiService } from '../../shared/services/api.service';
import { GRAPH_COLORS } from '../../shared/const';
import {
  Instrument,
  InstrumentForecastsGraphItem,
  InstrumentHistoryPrice,
  InstrumentInList,
  Operation,
  PredictionGraphResp, TechAnalysisResp
} from '../../shared/types';
import { getPriceByQuotation, getRoundPrice } from '../../utils';
import { CandleInterval } from '../../shared/enums';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';


@Component({
  selector: 'complex-graph-control',
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  providers: [PriceFormatPipe],
  templateUrl: './complex-graph-control.component.html',
  styleUrl: './complex-graph-control.component.scss'
})
export class ComplexGraphControlComponent {

  historyDaysCount = input(0, {transform: numberAttribute});
  interval = input<CandleInterval | null>(null);
  futureDaysCount = input(0, {transform: numberAttribute});

  onChange = output<{historyDaysCount: number, interval: CandleInterval, futureDaysCount: number}>();

  isPanelOpen = false;
  form = new FormGroup({
    historyDaysCount: new FormControl(),
    interval: new FormControl(),
    futureDaysCount: new FormControl(),
  });

  protected readonly candleInterval = CandleInterval;

  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.form.setValue({
        historyDaysCount: this.historyDaysCount(),
        interval: this.interval(),
        futureDaysCount: this.futureDaysCount(),
      }, { emitEvent: false });
    });

    this.form.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(value => this.onChange.emit({
        historyDaysCount: parseInt(value.historyDaysCount),
        interval: value.interval,
        futureDaysCount: parseInt(value.futureDaysCount),
      }));
  }

  handleTogglePanel(): void {
    this.isPanelOpen = !this.isPanelOpen;
  }
}

