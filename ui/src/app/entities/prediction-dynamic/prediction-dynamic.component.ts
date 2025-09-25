import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule } from '@angular/common';
import { combineLatest, firstValueFrom, map } from 'rxjs';
import { startOfDay, setHours, addDays } from 'date-fns';
import { InstrumentInList } from '../../shared/types';
import { ApiService } from '../../shared/services/api.service';
import { CurrentPriceService } from '../../shared/services/current-price.service';
import { PreloaderComponent } from '../preloader/preloader.component';
import { RelativeChangeToPercentPipe } from '../../shared/pipes/relative-change-to-percent.pipe';
import { DateDurationDaysPipe } from '../../shared/pipes/date-duration-days.pipe';
import { DaysCountHumanPipe } from '../../shared/pipes/days-count-human.pipe';

interface PredictionDynamicItem {
  prediction: number;
  date: Date;
}


@Component({
  selector: 'prediction-dynamic',
  imports: [CommonModule, PreloaderComponent, RelativeChangeToPercentPipe, DateDurationDaysPipe, DaysCountHumanPipe],
  providers: [],
  templateUrl: './prediction-dynamic.component.html',
  styleUrl: './prediction-dynamic.component.scss'
})
export class PredictionDynamicComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  currentPrice = resource<number | null, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.currentPriceService.getPriceByUid(params.request),
    )
  });

  predictions = resource<PredictionDynamicItem[], string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      combineLatest(
        this.predictionDates.map(
          date => this.apiService.getInstrumentPredictionConsensus(params.request, date)
            .pipe(
              map(consensus => ({
                prediction: consensus,
                date: date,
              } as PredictionDynamicItem)),
            )
        )
      ),
    )
  });

  private apiService = inject(ApiService);
  private currentPriceService = inject(CurrentPriceService);
  private predictionDates = [
    setHours(addDays(startOfDay(new Date()), 3), 12),
    setHours(addDays(startOfDay(new Date()), 7), 12),
    setHours(addDays(startOfDay(new Date()), 14), 12),
    setHours(addDays(startOfDay(new Date()), 21), 12),
    setHours(addDays(startOfDay(new Date()), 30), 12),
    setHours(addDays(startOfDay(new Date()), 60), 12),
    setHours(addDays(startOfDay(new Date()), 90), 12),
    setHours(addDays(startOfDay(new Date()), 180), 12),
    setHours(addDays(startOfDay(new Date()), 365), 12),
  ]

}
