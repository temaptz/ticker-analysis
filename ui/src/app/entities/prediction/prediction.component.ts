import { Component, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, combineLatest } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { Forecast, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { CurrentPriceService } from '../../shared/services/current-price.service';


@Component({
    selector: 'prediction',
    imports: [CommonModule, PreloaderComponent, PriceRoundPipe],
    providers: [],
    templateUrl: './prediction.component.html',
    styleUrl: './prediction.component.scss'
})
export class PredictionComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  isPlus = signal<boolean>(false);
  percent = signal<number>(0);
  prediction = signal<Forecast>(null);
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
        .subscribe(([forecast, currentPrice]: [Forecast, number | null]) => {
          const current = currentPrice ?? 0;
          const prediction = forecast ?? 0;
          const absPercentChange = Math.round(Math.abs(prediction - current) / current * 100) / 100;
          const isPlus = prediction - current >= 0;

          this.prediction.set(prediction);
          this.isPlus.set(isPlus);
          this.percent.set(absPercentChange);
        });
    });
  }

}
