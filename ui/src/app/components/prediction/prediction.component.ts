import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { AppService } from '../../app.service';
import { Forecast, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PricePipe } from '../../pipes/price.pipe';


@Component({
    selector: 'prediction',
    imports: [CommonModule, PreloaderComponent, PricePipe],
    providers: [],
    templateUrl: './prediction.component.html',
    styleUrl: './prediction.component.scss'
})
export class PredictionComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  currentPrice = input.required<number | null>();

  isLoaded = signal<boolean>(false);
  isPlus = signal<boolean>(false);
  percent = signal<number>(0);
  prediction = signal<Forecast>(null);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {
    effect(() => {
      this.appService.getInstrumentPrediction(this.instrumentUid())
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe((resp: Forecast) => {
          const current = this.currentPrice() ?? 0;
          const prediction = resp ?? 0;
          const absPercentChange = Math.round(Math.abs(prediction - current) / current * 100) / 100;
          const isPlus = prediction - current >= 0;

          this.prediction.set(prediction);
          this.isPlus.set(isPlus);
          this.percent.set(absPercentChange);

          this.appService.predictionPercentByUidMap.set(this.instrumentUid(), absPercentChange*(isPlus ? 1 : -1));
        });
    }, { allowSignalWrites: true });
  }

}
