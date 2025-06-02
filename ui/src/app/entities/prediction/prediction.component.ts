import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { combineLatest, finalize } from 'rxjs';
import { InstrumentInList, PredictionResp } from '../../shared/types';
import { ModelNameEnum } from '../../shared/enums';
import { ApiService } from '../../shared/services/api.service';
import { CurrentPriceService } from '../../shared/services/current-price.service';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PredictionItemComponent } from '../prediction-item/prediction-item.component';


@Component({
  selector: 'prediction',
  imports: [CommonModule, PreloaderComponent, PredictionItemComponent],
  providers: [],
  templateUrl: './prediction.component.html',
  styleUrl: './prediction.component.scss'
})
export class PredictionComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  predictionResp = signal<PredictionResp | null>(null);
  currentPrice = signal<number | null>(null);

  modelNames: ModelNameEnum[] = [ModelNameEnum.Ta_1, ModelNameEnum.Ta_1_1, ModelNameEnum.Ta_1_2, ModelNameEnum.Ta_2, ModelNameEnum.Ta_2_1];

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
        .subscribe(([predictions, currentPrice]: [PredictionResp, number | null]) => {
          this.predictionResp.set(predictions);
          this.currentPrice.set(currentPrice);
        });
    });
  }

}
