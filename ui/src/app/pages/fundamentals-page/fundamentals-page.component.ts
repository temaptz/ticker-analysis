import { Component, effect, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { FundamentalsHistory, Instrument } from '../../types';
import { FundamentalsCardComponent } from '../../entities/fundamentals-card/fundamentals-card.component';
import { InstrumentLogoComponent } from '../../entities/instrument-logo/instrument-logo.component';
import { FundamentalsComponent } from '../../entities/fundamentals/fundamentals.component';


@Component({
  selector: 'fundamentals-page',
  imports: [CommonModule, PreloaderComponent, FundamentalsCardComponent, InstrumentLogoComponent, FundamentalsComponent],
  providers: [],
  templateUrl: './fundamentals-page.component.html',
  styleUrl: './fundamentals-page.component.scss'
})
export class FundamentalsPageComponent {

  isLoadedInstrument = signal<boolean>(false);
  isLoadedHistory = signal<boolean>(false);
  instrumentUid = signal<string>('');
  instrument = signal<Instrument | null>(null);
  history = signal<FundamentalsHistory[]>([]);

  constructor(
    private appService: ApiService,
    private activatedRoute: ActivatedRoute
  ) {
    this.instrumentUid.set(
      this.activatedRoute.snapshot.params['instrumentUid']
    );

    effect(() => {
      this.appService.getInstrument(
        this.instrumentUid(),
      )
        .pipe(finalize(() => this.isLoadedInstrument.set(true)))
        .subscribe(resp => this.instrument.set(resp));
    });

    effect(() => {
      const assetUid = this.instrument()?.asset_uid

      if (assetUid) {
        this.appService.getInstrumentFundamentalsHistory(assetUid)
          .pipe(finalize(() => this.isLoadedHistory.set(true)))
          .subscribe(resp => this.history.set(resp));
      }
    });
  }

  protected readonly Object = Object;
}
