import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { AppService } from '../../app.service';
import { Fundamentals, InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';
import { PriceFormatPipe } from '../../pipes/price-format.pipe';


@Component({
  selector: 'fundamentals',
  imports: [CommonModule, PreloaderComponent, PriceFormatPipe],
  providers: [],
  templateUrl: './fundamentals.component.html',
  styleUrl: './fundamentals.component.scss'
})
export class FundamentalsComponent implements OnInit {

  @Input({required: true}) instrumentAssetUid!: InstrumentInList['asset_uid'];

  isLoaded = signal<boolean>(false);
  fundamentals = signal<Fundamentals>(null);
  getPriceByQuotation = getPriceByQuotation;

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentFundamentals(this.instrumentAssetUid)
      .pipe(finalize(() => this.isLoaded.set(true)))
      .subscribe((resp: Fundamentals) => this.fundamentals.set(resp));
  }

}
