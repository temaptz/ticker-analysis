import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize, combineLatest } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { PriceRoundPipe } from '../../shared/pipes/price-round.pipe';
import { PreloaderComponent } from '../preloader/preloader.component';
import { CurrentPriceService } from '../../shared/services/current-price.service';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { GRAPH_COLORS } from '../../shared/const';
import { Forecast, InstrumentInList } from '../../types';


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
  isPlus_ta_1_2 = signal<boolean>(false);
  isPlus_ta_2 = signal<boolean>(false);
  isPlus_consensus = signal<boolean>(false);
  percent_ta_1 = signal<number>(0);
  percent_ta_1_1 = signal<number>(0);
  percent_ta_1_2 = signal<number>(0);
  percent_ta_2 = signal<number>(0);
  percent_consensus = signal<number>(0);
  prediction_ta_1 = signal<number | null>(null);
  prediction_ta_1_1 = signal<number | null>(null);
  prediction_ta_1_2 = signal<number | null>(null);
  prediction_ta_2 = signal<number | null>(null);
  prediction_consensus = signal<number | null>(null);
  colors = GRAPH_COLORS;

  private apiService = inject(ApiService);
  private currentPriceService = inject(CurrentPriceService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      const uid = this.instrumentUid();
      combineLatest([
        this.apiService.getInstrumentPrediction(uid),
        this.currentPriceService.getPriceByUid(uid),
      ])
        .pipe(
          finalize(() => this.isLoaded.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe(([predictions, currentPrice]: [Forecast, number | null]) => {
          const current = currentPrice ?? 0;
          const prediction_ta_1 = predictions['ta-1'] ?? 0;
          const prediction_ta_1_1 = predictions['ta-1_1'] ?? 0;
          const prediction_ta_1_2 = predictions['ta-1_2'] ?? 0;
          const prediction_ta_2 = predictions['ta-2'] ?? 0;
          const prediction_consensus = predictions['consensus'] ?? 0;
          const absPercentChange_ta_1 = Math.round(Math.abs(prediction_ta_1 - current) / current * 10000) / 100;
          const absPercentChange_ta_1_1 = Math.round(Math.abs(prediction_ta_1_1 - current) / current * 10000) / 100;
          const absPercentChange_ta_1_2 = Math.round(Math.abs(prediction_ta_1_2 - current) / current * 10000) / 100;
          const absPercentChange_ta_2 = Math.round(Math.abs(prediction_ta_2 - current) / current * 10000) / 100;
          const absPercentChange_consensus = Math.round(Math.abs(prediction_consensus - current) / current * 10000) / 100;
          const isPlus_ta_1 = prediction_ta_1 - current >= 0;
          const isPlus_ta_1_1 = prediction_ta_1_1 - current >= 0;
          const isPlus_ta_1_2 = prediction_ta_1_2 - current >= 0;
          const isPlus_ta_2 = prediction_ta_2 - current >= 0;
          const isPlus_consensus = prediction_consensus - current >= 0;

          this.prediction_ta_1.set(prediction_ta_1);
          this.isPlus_ta_1.set(isPlus_ta_1);
          this.percent_ta_1.set(absPercentChange_ta_1);

          this.prediction_ta_1_1.set(prediction_ta_1_1);
          this.isPlus_ta_1_1.set(isPlus_ta_1_1);
          this.percent_ta_1_1.set(absPercentChange_ta_1_1);

          this.prediction_ta_1_2.set(prediction_ta_1_2);
          this.isPlus_ta_1_2.set(isPlus_ta_1_2);
          this.percent_ta_1_2.set(absPercentChange_ta_1_2);

          this.prediction_ta_2.set(prediction_ta_2);
          this.isPlus_ta_2.set(isPlus_ta_2);
          this.percent_ta_2.set(absPercentChange_ta_2);

          this.prediction_consensus.set(prediction_consensus);
          this.isPlus_consensus.set(isPlus_consensus);
          this.percent_consensus.set(absPercentChange_consensus);
        });
    });
  }

}
