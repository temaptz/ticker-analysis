import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { Fundamentals, InstrumentInList } from '../../types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { FundamentalsCardComponent } from '../fundamentals-card/fundamentals-card.component';


@Component({
  selector: 'fundamentals',
  imports: [CommonModule, PreloaderComponent, RouterLink, FundamentalsCardComponent],
  providers: [],
  templateUrl: './fundamentals.component.html',
  styleUrl: './fundamentals.component.scss'
})
export class FundamentalsComponent {

  instrumentAssetUid = input.required<InstrumentInList['asset_uid']>();
  instrumentUid = input<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  fundamentals = signal<Fundamentals>(null);

  constructor(
    private appService: ApiService,
  ) {
    effect(() => {
      this.appService.getInstrumentFundamentals(this.instrumentAssetUid())
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe((resp: Fundamentals) => this.fundamentals.set(resp));
    });
  }

}
