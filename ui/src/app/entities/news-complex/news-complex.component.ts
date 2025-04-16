import { Component, effect, input,  signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { combineLatest, finalize } from 'rxjs';
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
    effect(() => combineLatest([
      ...this.weeks.map(([from, to]) =>
        this.appService.getInstrumentNewsRate(this.instrumentUid(), from, to))
    ])
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: NewsRateResponse[]) => this.weeksResponse.set(resp?.filter(_ => !!_))));
  }

  protected readonly Object = Object;
}
