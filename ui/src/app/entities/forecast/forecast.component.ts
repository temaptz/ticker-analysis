import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../shared/services/api.service';
import { Forecast, InstrumentHistoryPrice, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { finalize } from 'rxjs';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
    selector: 'forecast',
    imports: [CommonModule, PreloaderComponent],
    providers: [],
    templateUrl: './forecast.component.html',
    styleUrl: './forecast.component.scss'
})
export class ForecastComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  isLoaded = signal<boolean>(false);
  forecast = signal<Forecast>(null);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: ApiService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentConsensusForecast(this.instrumentUid)
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: Forecast) => this.forecast.set(resp));
  }

}
