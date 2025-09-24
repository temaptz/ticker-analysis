import {
  booleanAttribute,
  Component,
  DestroyRef,
  effect,
  inject,
  input,
  numberAttribute,
  output,
} from '@angular/core';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { TechAnalysisOptions } from '../../shared/types';
import { CandleInterval, ModelNameEnum } from '../../shared/enums';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';

export interface ComplexGraphControlOptions {
  historyDaysCount: number,
  interval: CandleInterval,
  futureDaysCount: number,
  isShowNews: boolean,
  isShowTa_1_PredictionsHistory: boolean,
  isShowTa_1_1_PredictionsHistory: boolean,
  isShowTa_1_2_PredictionsHistory: boolean,
  isShowTa_2_PredictionsHistory: boolean,
  isShowTa_2_1_PredictionsHistory: boolean,
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
  isShowTa_1_PredictionsHistory = input(false, {transform: booleanAttribute});
  isShowTa_1_1_PredictionsHistory = input(false, {transform: booleanAttribute});
  isShowTa_1_2_PredictionsHistory = input(false, {transform: booleanAttribute});
  isShowTa_2_PredictionsHistory = input(false, {transform: booleanAttribute});
  isShowTa_2_1_PredictionsHistory = input(false, {transform: booleanAttribute});
  isShowModels = input(false, {transform: booleanAttribute});

  onChange = output<ComplexGraphControlOptions>();
  onChangeTechAnalysis = output<TechAnalysisOptions>();

  isPanelOpen = false;
  form = new FormGroup({
    historyDaysCount: new FormControl(),
    interval: new FormControl(),
    futureDaysCount: new FormControl(),
    isShowNews: new FormControl<boolean>(this.isShowNews()),
    isShowTa_1_PredictionsHistory: new FormControl<boolean>(this.isShowTa_1_PredictionsHistory()),
    isShowTa_1_1_PredictionsHistory: new FormControl<boolean>(this.isShowTa_1_1_PredictionsHistory()),
    isShowTa_1_2_PredictionsHistory: new FormControl<boolean>(this.isShowTa_1_2_PredictionsHistory()),
    isShowTa_2_PredictionsHistory: new FormControl<boolean>(this.isShowTa_2_PredictionsHistory()),
    isShowTa_2_1_PredictionsHistory: new FormControl<boolean>(this.isShowTa_2_1_PredictionsHistory()),
    isShowModels: new FormControl<boolean>(this.isShowModels()),
  });

  protected readonly candleInterval = CandleInterval;
  protected readonly modelNameEnum = ModelNameEnum;

  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.form.setValue({
        historyDaysCount: this.historyDaysCount(),
        interval: this.interval(),
        futureDaysCount: this.futureDaysCount(),
        isShowNews: this.isShowNews(),
        isShowTa_1_PredictionsHistory:  this.isShowTa_1_PredictionsHistory(),
        isShowTa_1_1_PredictionsHistory:  this.isShowTa_1_1_PredictionsHistory(),
        isShowTa_1_2_PredictionsHistory:  this.isShowTa_1_2_PredictionsHistory(),
        isShowTa_2_PredictionsHistory:  this.isShowTa_2_PredictionsHistory(),
        isShowTa_2_1_PredictionsHistory:  this.isShowTa_2_1_PredictionsHistory(),
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
        isShowTa_1_PredictionsHistory: !!value.isShowTa_1_PredictionsHistory,
        isShowTa_1_1_PredictionsHistory: !!value.isShowTa_1_1_PredictionsHistory,
        isShowTa_1_2_PredictionsHistory: !!value.isShowTa_1_2_PredictionsHistory,
        isShowTa_2_PredictionsHistory: !!value.isShowTa_2_PredictionsHistory,
        isShowTa_2_1_PredictionsHistory: !!value.isShowTa_2_1_PredictionsHistory,
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

