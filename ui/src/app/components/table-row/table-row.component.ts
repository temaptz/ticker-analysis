import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { Instrument, InstrumentInList, InstrumentLastPrice } from '../../types';
import { isBefore, parse, parseJSON } from 'date-fns';
import { GraphComponent } from '../graph/graph.component';
import { CandleInterval } from '../../enums';
import { getPriceByQuotation } from '../../utils';
import { ForecastComponent } from '../forecast/forecast.component';
import { ForecastHistoryComponent } from '../forecast-history/forecast-history.component';
import { FundamentalsComponent } from '../fundamentals/fundamentals.component';

@Component({
  selector: '[app-table-row]',
  standalone: true,
  imports: [CommonModule, GraphComponent, ForecastComponent, ForecastHistoryComponent, FundamentalsComponent],
  templateUrl: './table-row.component.html',
  styleUrl: './table-row.component.scss'
})
export class TableRowComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];

  instrument = signal<Instrument>(null);
  instrumentLastPrice = signal<InstrumentLastPrice>(null);
  candleInterval = CandleInterval;
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrument(this.instrumentUid)
      .subscribe(resp => this.instrument.set(resp));

    this.appService.getInstrumentLastPrices(this.instrumentUid)
      .subscribe(resp => {
        const price = resp
          ?.sort((a, b) => parseJSON(a.time).getTime() - parseJSON(b.time).getTime())
          ?.[0];

        this.instrumentLastPrice.set(price);
      });
  }

}
