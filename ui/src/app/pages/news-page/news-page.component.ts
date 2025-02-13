import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { PreloaderComponent } from '../../components/preloader/preloader.component';
import { NewsContentResponse } from '../../types';
import { ActivatedRoute } from '@angular/router';
import { subDays } from 'date-fns';
import { finalize } from 'rxjs';


@Component({
  selector: 'news-page',
  standalone: true,
  imports: [CommonModule, PreloaderComponent],
  providers: [],
  templateUrl: './news-page.component.html',
  styleUrl: './news-page.component.scss'
})
export class NewsPageComponent implements OnInit {

  isLoaded = signal<boolean>(false);
  news = signal<NewsContentResponse | null>(null);
  dateFrom = subDays(new Date(), 7);
  dateTo = new Date();

  constructor(
    private appService: AppService,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit() {
    this.appService.getInstrumentNewsContent(
      this.activatedRoute.snapshot.params['instrumentUid'],
      this.dateFrom,
      this.dateTo
    )
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.news.set(resp));
  }

  protected readonly Object = Object;
}
