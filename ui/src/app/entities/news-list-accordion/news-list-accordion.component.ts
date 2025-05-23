import { Component, computed, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatExpansionModule } from '@angular/material/expansion';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { NewsListRatedResponse } from '../../shared/types';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { NewsBarComponent } from '../../entities/news-bar/news-bar.component';
import { HighlightWordsPipe } from '../../shared/pipes/highlight-words.pipe';
import { RateV2Component } from '../rate-v2/rate-v2.component';


@Component({
  selector: 'news-list-accordion',
  imports: [CommonModule, PreloaderComponent, MatExpansionModule, NewsBarComponent, HighlightWordsPipe, RateV2Component],
  providers: [],
  templateUrl: './news-list-accordion.component.html',
  styleUrl: './news-list-accordion.component.scss'
})
export class NewsListAccordionComponent {

  instrumentUid = input.required<string>();

  isLoaded = signal<boolean>(false);
  news = signal<NewsListRatedResponse | null>(null);
  dateFrom = startOfDay(subDays(new Date(), 30));
  dateTo = endOfDay(new Date());

  keywords = computed<string[]>(() => this.news()?.keywords ?? []);

  private appService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      const instrumentUid = this.instrumentUid();

      this.appService.getInstrumentNewsListRated(
        instrumentUid,
        this.dateFrom,
        this.dateTo,
      )
        .pipe(
          finalize(() => this.isLoaded.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe(resp => this.news.set(resp));
    });
  }

}
