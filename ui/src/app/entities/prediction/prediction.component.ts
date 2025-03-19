import { Component, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, combineLatest } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { Forecast, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { CurrentPriceService } from '../../shared/services/current-price.service';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';


@Component({
    selector: 'prediction',
  imports: [CommonModule, PreloaderComponent, PriceRoundPipe, PriceFormatPipe],
    providers: [],
    templateUrl: './prediction.component.html',
    styleUrl: './prediction.component.scss'
})
export class PredictionComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  isPlus_ta_1 = signal<boolean>(false);
  isPlus_ta_1_1 = signal<boolean>(false);
  percent_ta_1 = signal<number>(0);
  percent_ta_1_1 = signal<number>(0);
  prediction_ta_1 = signal<number | null>(null);
  prediction_ta_1_1 = signal<number | null>(null);
  getPriceByQuotation = getPriceByQuotation;

  private apiService = inject(ApiService);
  private currentPriceService = inject(CurrentPriceService);

  constructor() {
    effect(() => {
      const uid = this.instrumentUid();
      combineLatest([
        this.apiService.getInstrumentPrediction(uid),
        this.currentPriceService.getPriceByUid(uid),
      ])
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe(([predictions, currentPrice]: [Forecast, number | null]) => {
          const current = currentPrice ?? 0;
          const prediction_ta_1 = predictions['ta-1'] ?? 0;
          const prediction_ta_1_1 = predictions['ta-1_1'] ?? 0;
          const absPercentChange_ta_1 = Math.round(Math.abs(prediction_ta_1 - current) / current * 100) / 100;
          const absPercentChange_ta_1_1 = Math.round(Math.abs(prediction_ta_1_1 - current) / current * 100) / 100;
          const isPlus_ta_1 = prediction_ta_1 - current >= 0;
          const isPlus_ta_1_1 = prediction_ta_1_1 - current >= 0;

          this.prediction_ta_1.set(prediction_ta_1);
          this.isPlus_ta_1.set(isPlus_ta_1);
          this.percent_ta_1.set(absPercentChange_ta_1);

          this.prediction_ta_1_1.set(prediction_ta_1_1);
          this.isPlus_ta_1_1.set(isPlus_ta_1_1);
          this.percent_ta_1_1.set(absPercentChange_ta_1_1);
        });
    });
  }

}
