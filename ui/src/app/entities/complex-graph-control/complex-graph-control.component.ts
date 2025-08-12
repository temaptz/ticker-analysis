import {
  booleanAttribute,
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
  PredictionGraphResp, TechAnalysisOptions, TechAnalysisResp
} from '../../shared/types';
import { getPriceByQuotation, getRoundPrice } from '../../utils';
import { CandleInterval } from '../../shared/enums';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { EchartsGraphComponent } from '../echarts-graph/echarts-graph.component';
import { ECHARTS_MAIN_OPTIONS } from '../echarts-graph/utils';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';

export interface ComplexGraphControlOptions {
  historyDaysCount: number,
  interval: CandleInterval,
  futureDaysCount: number,
  isShowNews: boolean,
  isShowPredictionsHistory: boolean,
  isShowModels: boolean
}


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
  isShowTechAnalysis = input(false, {transform: booleanAttribute});
  techAnalysisOptions = input<TechAnalysisOptions>({});
  isShowNews = input(false, {transform: booleanAttribute});
  isShowPredictionsHistory = input(false, {transform: booleanAttribute});
  isShowModels = input(false, {transform: booleanAttribute});

  onChange = output<ComplexGraphControlOptions>();
  onChangeTechAnalysis = output<TechAnalysisOptions>();

  isPanelOpen = false;
  form = new FormGroup({
    historyDaysCount: new FormControl(),
    interval: new FormControl(),
    futureDaysCount: new FormControl(),
    isShowNews: new FormControl<boolean>(this.isShowNews()),
    isShowPredictionsHistory: new FormControl<boolean>(this.isShowPredictionsHistory()),
    isShowModels: new FormControl<boolean>(this.isShowModels()),
  });

  protected readonly candleInterval = CandleInterval;

  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.form.setValue({
        historyDaysCount: this.historyDaysCount(),
        interval: this.interval(),
        futureDaysCount: this.futureDaysCount(),
        isShowNews: this.isShowNews(),
        isShowPredictionsHistory:  this.isShowPredictionsHistory(),
        isShowModels: this.isShowModels(),
      }, { emitEvent: false });
    });

    this.form.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(value => this.onChange.emit({
        historyDaysCount: parseInt(value.historyDaysCount),
        interval: value.interval,
        futureDaysCount: parseInt(value.futureDaysCount),
        isShowNews: !!value.isShowNews,
        isShowPredictionsHistory: !!value.isShowPredictionsHistory,
        isShowModels: !!value.isShowModels,
      }));
  }

  handleTogglePanel(): void {
    this.isPanelOpen = !this.isPanelOpen;
  }

  handleChangeTechAnalysisOption(optionName: keyof TechAnalysisOptions, value: any): void {
    const nextOptions = this.techAnalysisOptions();
    nextOptions[optionName] = value;

    this.onChangeTechAnalysis.emit(nextOptions);
  }

  handleToggleBoolean(optionName: string, event: Event): void {
    const value: boolean = !!(event.target as HTMLInputElement)?.checked
    const formPatch: any = {};
    formPatch[optionName] = value;
    this.form.patchValue(formPatch);
  }

}

