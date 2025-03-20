import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentForecastsHistory, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { parseJSON, isSameMonth } from 'date-fns';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
    selector: 'forecast-history',
    imports: [CommonModule, PreloaderComponent],
    providers: [],
    templateUrl: './forecast-history.component.html',
    styleUrl: './forecast-history.component.scss'
})
export class ForecastHistoryComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  isLoaded = signal<boolean>(false);
  history = signal<InstrumentForecastsHistory[]>([]);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: ApiService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentHistoryForecasts(this.instrumentUid)
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: InstrumentForecastsHistory[]) => this.history.set(resp));
  }

}
