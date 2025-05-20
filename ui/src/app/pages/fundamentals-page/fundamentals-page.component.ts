import { Component, DestroyRef, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { PreloaderComponent } from '../../entities/preloader/preloader.component';
import { FundamentalsHistory, Instrument } from '../../shared/types';
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
  ticker = signal<string>('');
  instrument = signal<Instrument | null>(null);
  history = signal<FundamentalsHistory[]>([]);

  private apiService = inject(ApiService);
  private activatedRoute = inject(ActivatedRoute);
  private destroyRef = inject(DestroyRef);

  constructor() {
    this.ticker.set(
      this.activatedRoute.snapshot.params['ticker']
    );

    effect(() => {
      this.apiService.getInstrument(undefined, this.ticker())
        .pipe(
          finalize(() => this.isLoadedInstrument.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe(resp => this.instrument.set(resp));
    });

    effect(() => {
      const assetUid = this.instrument()?.asset_uid

      if (assetUid) {
        this.apiService.getInstrumentFundamentalsHistory(assetUid)
          .pipe(
            finalize(() => this.isLoadedHistory.set(true)),
            takeUntilDestroyed(this.destroyRef),
          )
          .subscribe(resp => this.history.set(resp));
      }
    });
  }

  protected readonly Object = Object;
}
