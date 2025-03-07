import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../shared/services/api.service';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { NewsResponse } from '../../types';
import { ActivatedRoute } from '@angular/router';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { finalize } from 'rxjs';
import {
  InstrumentComplexInfoComponent
} from '../../widgets/instrument-complex-info/instrument-complex-info.component';
import { NewsBarComponent } from '../../entities/news-bar/news-bar.component';


@Component({
    selector: 'instrument',
  imports: [CommonModule, PreloaderComponent, InstrumentComplexInfoComponent, NewsBarComponent],
    providers: [],
    templateUrl: './instrument.component.html',
    styleUrl: './instrument.component.scss'
})
export class InstrumentComponent implements OnInit {

  isLoaded = signal<boolean>(false);
  instrumentUid = signal<string>('');
  news = signal<NewsResponse | null>(null);
  dateFrom = startOfDay(subDays(new Date(), 6));
  dateTo = endOfDay(new Date());

  constructor(
    private appService: ApiService,
    private activatedRoute: ActivatedRoute
  ) {
    this.instrumentUid.set(
      this.activatedRoute.snapshot.params['instrumentUid']
    );
  }

  ngOnInit() {
    this.appService.getInstrumentNews(
      this.instrumentUid(),
      this.dateFrom,
      this.dateTo,
      true,
    )
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.news.set(resp));
  }

  protected readonly Object = Object;
}
