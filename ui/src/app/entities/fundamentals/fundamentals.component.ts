import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { Fundamentals, InstrumentInList } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { FundamentalsCardComponent } from '../fundamentals-card/fundamentals-card.component';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';


@Component({
  selector: 'fundamentals',
  imports: [CommonModule, PreloaderComponent, RouterLink, FundamentalsCardComponent],
  providers: [],
  templateUrl: './fundamentals.component.html',
  styleUrl: './fundamentals.component.scss'
})
export class FundamentalsComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  ticker = input<InstrumentInList['ticker']>();

  isLoaded = signal<boolean>(false);
  fundamentals = signal<Fundamentals>(null);

  private apiService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.apiService.getInstrumentFundamentals(this.instrumentUid())
        .pipe(
          finalize(() => this.isLoaded.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe((resp: Fundamentals) => this.fundamentals.set(resp));
    });
  }

}
