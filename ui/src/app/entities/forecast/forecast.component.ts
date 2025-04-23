import { Component, DestroyRef, inject, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { PriceFormatPipe } from '../../shared/pipes/price-format.pipe';
import { Forecast, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
    selector: 'forecast',
  imports: [CommonModule, PreloaderComponent, PriceFormatPipe],
    providers: [],
    templateUrl: './forecast.component.html',
    styleUrl: './forecast.component.scss'
})
export class ForecastComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  isLoaded = signal<boolean>(false);
  forecast = signal<Forecast>(null);
  getPriceByQuotation = getPriceByQuotation;

  private apiService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    this.apiService.getInstrumentConsensusForecast(this.instrumentUid)
      .pipe(
        finalize(() => this.isLoaded.set(true)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((resp: Forecast) => this.forecast.set(resp));
  }

}
