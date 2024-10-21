import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { Instrument, InstrumentInList, InstrumentLastPrice } from '../../types';
import { isBefore, parse, parseJSON } from 'date-fns';

@Component({
  selector: '[app-table-row]',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './table-row.component.html',
  styleUrl: './table-row.component.scss'
})
export class TableRowComponent implements OnInit {

  @Input() instrumentUid: InstrumentInList['uid'];

  instrument = signal<Instrument>(null);
  instrumentLastPrice = signal<InstrumentLastPrice>(null);

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrument(this.instrumentUid)
      .subscribe(resp => this.instrument.set(resp));

    this.appService.getInstrumentLastPrice(this.instrumentUid)
      .subscribe(resp => {
        const price = resp
          ?.sort((a, b) => parseJSON(a.time).getTime() - parseJSON(b.time).getTime())
          ?.[0];

        this.instrumentLastPrice.set(price);
      });
  }

}
