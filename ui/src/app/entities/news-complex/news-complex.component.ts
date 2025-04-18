import { Component, effect, input,  signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize, forkJoin, of } from 'rxjs';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, NewsRateResponse } from '../../types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { NewsBarComponent } from '../news-bar/news-bar.component';


@Component({
  selector: 'news-complex',
  imports: [CommonModule, PreloaderComponent, NewsBarComponent],
  providers: [],
  templateUrl: './news-complex.component.html',
  styleUrl: './news-complex.component.scss'
})
export class NewsComplexComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  weeksResponse = signal<NewsRateResponse[]>([]);

  weeks: [Date, Date][] = [
    [startOfDay(subDays(new Date(), 6)), endOfDay(new Date())],
    [startOfDay(subDays(new Date(), 13)), endOfDay(subDays(new Date(), 7))],
    [startOfDay(subDays(new Date(), 20)), endOfDay(subDays(new Date(), 14))],
    [startOfDay(subDays(new Date(), 27)), endOfDay(subDays(new Date(), 21))],
  ];

  constructor(
    private appService: ApiService,
  ) {
    effect(() => forkJoin([
      ...this.weeks.map(([from, to]) => forkJoin([
          this.appService.getInstrumentNewsRate(this.instrumentUid(), from, to),
          of<[Date, Date]>([from, to]),
        ])
      )
    ])
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: [NewsRateResponse | null, [Date, Date]][]) => {
        this.weeksResponse.set(resp.map(i => {
          const keywords = resp?.find(j => j?.[0]?.keywords?.length)?.[0]?.keywords ?? [];

          return {
            ...(i[0] ?? {}),
            start_date: i[1][0],
            end_date: i[1][1],
            keywords,
          } as NewsRateResponse;
        }));
      }));
  }

  protected readonly Object = Object;
}
