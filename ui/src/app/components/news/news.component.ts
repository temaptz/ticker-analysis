import { Component, effect, input,  signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { InstrumentInList, NewsResponse } from '../../types';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceByQuotationPipe } from '../../pipes/price-by-quotation.pipe';
import { PricePipe } from '../../pipes/price.pipe';
import { subDays } from 'date-fns';


@Component({
  selector: 'news',
  standalone: true,
  imports: [CommonModule, PreloaderComponent, PriceByQuotationPipe, PricePipe],
  providers: [],
  templateUrl: './news.component.html',
  styleUrl: './news.component.scss'
})
export class NewsComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  news = signal<NewsResponse | null>(null);
  dateFrom = subDays(new Date(), 7);
  dateTo = new Date();
  barHeightMultiply = 2

  constructor(
    private appService: AppService,
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
