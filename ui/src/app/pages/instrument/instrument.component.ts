import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { NewsContentResponse } from '../../types';
import { ActivatedRoute } from '@angular/router';
import { subDays } from 'date-fns';
import { finalize } from 'rxjs';
import {
  InstrumentComplexInfoComponent
} from '../../entities/instrument-complex-info/instrument-complex-info.component';


@Component({
    selector: 'instrument',
    imports: [CommonModule, PreloaderComponent, InstrumentComplexInfoComponent],
    providers: [],
    templateUrl: './instrument.component.html',
    styleUrl: './instrument.component.scss'
})
export class InstrumentComponent implements OnInit {

  isLoaded = signal<boolean>(false);
  instrumentUid = signal<string>('');
  news = signal<NewsContentResponse | null>(null);
  dateFrom = subDays(new Date(), 7);
  dateTo = new Date();

  constructor(
    private appService: AppService,
    private activatedRoute: ActivatedRoute
  ) {
    this.instrumentUid.set(
      this.activatedRoute.snapshot.params['instrumentUid']
    );
  }

  ngOnInit() {
    this.appService.getInstrumentNewsContent(
      this.instrumentUid(),
      this.dateFrom,
      this.dateTo
    )
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe(resp => this.news.set(resp));
  }

  protected readonly Object = Object;
}
