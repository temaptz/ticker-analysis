import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { Forecast, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';


@Component({
  selector: 'forecast-history',
  standalone: true,
  imports: [CommonModule],
  providers: [],
  templateUrl: './forecast-history.component.html',
  styleUrl: './forecast-history.component.scss'
})
export class ForecastHistoryComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  history = signal<Forecast[]>([]);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentHistoryForecasts(this.instrumentUid)
      .subscribe((resp: Forecast[]) => this.history.set(resp));
  }

}
