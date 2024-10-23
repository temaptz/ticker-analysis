import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { Forecast, InstrumentHistoryPrice, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';


@Component({
  selector: 'forecast',
  standalone: true,
  imports: [CommonModule],
  providers: [],
  templateUrl: './forecast.component.html',
  styleUrl: './forecast.component.scss'
})
export class ForecastComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  forecast = signal<Forecast>(null);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentConsensusForecast(this.instrumentUid)
      .subscribe((resp: Forecast) => this.forecast.set(resp));
  }

}
