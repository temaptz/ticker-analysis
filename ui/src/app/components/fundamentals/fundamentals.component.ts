import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { Fundamentals, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';


@Component({
  selector: 'fundamentals',
  standalone: true,
  imports: [CommonModule],
  providers: [],
  templateUrl: './fundamentals.component.html',
  styleUrl: './fundamentals.component.scss'
})
export class FundamentalsComponent implements OnInit {

  @Input({required: true}) instrumentAssetUid!: InstrumentInList['asset_uid'];

  fundamentals = signal<Fundamentals>(null);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentFundamentals(this.instrumentAssetUid)
      .subscribe((resp: Fundamentals) => this.fundamentals.set(resp));
  }

}
