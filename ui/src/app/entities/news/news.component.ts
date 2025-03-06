import { Component, effect, input,  signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, NewsResponse } from '../../types';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { endOfDay, setHours, startOfDay, subDays } from 'date-fns';


@Component({
    selector: 'news',
    imports: [CommonModule, PreloaderComponent],
    providers: [],
    templateUrl: './news.component.html',
    styleUrl: './news.component.scss'
})
export class NewsComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  news = signal<NewsResponse | null>(null);
  dateFrom = startOfDay(subDays(new Date(), 6));
  dateTo = endOfDay(new Date());

  constructor(
    private appService: ApiService,
  ) {
    effect(() => this.appService.getInstrumentNews(
      this.instrumentUid(),
      this.dateFrom,
      this.dateTo,
    )
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: NewsResponse) => this.news.set(resp)));
  }

  protected readonly Object = Object;
}
