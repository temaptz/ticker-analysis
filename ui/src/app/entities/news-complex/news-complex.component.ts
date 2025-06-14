import { Component, DestroyRef, effect, inject, input, resource, ResourceLoaderParams, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize, firstValueFrom, forkJoin, lastValueFrom, map, of } from 'rxjs';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, NewsListRatedResponse } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { NewsBarComponent } from '../news-bar/news-bar.component';
import { RateV2Component } from '../rate-v2/rate-v2.component';


@Component({
  selector: 'news-complex',
  imports: [CommonModule, PreloaderComponent, NewsBarComponent, RateV2Component],
  providers: [],
  templateUrl: './news-complex.component.html',
  styleUrl: './news-complex.component.scss'
})
export class NewsComplexComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);

  weeksResource = resource<NewsListRatedResponse[], string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      forkJoin([
        ...this.weeks.map(([from, to]) => this.apiService.getInstrumentNewsListRated(params.request, from, to)
        )
      ])
    )
  });

  weeks: [Date, Date][] = [
    [startOfDay(subDays(new Date(), 6)), endOfDay(new Date())],
    [startOfDay(subDays(new Date(), 13)), endOfDay(subDays(new Date(), 7))],
    [startOfDay(subDays(new Date(), 20)), endOfDay(subDays(new Date(), 14))],
    [startOfDay(subDays(new Date(), 27)), endOfDay(subDays(new Date(), 21))],
    [startOfDay(subDays(new Date(), 27)), endOfDay(new Date())],
  ];

  private apiService = inject(ApiService);

  protected readonly Object = Object;
}
