import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, NewsResponse } from '../../types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { NewsBarComponent } from '../news-bar/news-bar.component';


@Component({
    selector: 'news',
  imports: [CommonModule, PreloaderComponent, NewsBarComponent],
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

  private apiService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => this.apiService.getInstrumentNews(
      this.instrumentUid(),
      this.dateFrom,
      this.dateTo,
    )
      .pipe(
        finalize(() => this.isLoaded.set(true)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((resp: NewsResponse) => this.news.set(resp)));
  }

  protected readonly Object = Object;
}
