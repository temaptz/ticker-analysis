import { Component, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList } from '../../types';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
    selector: 'current-price',
    imports: [CommonModule, PreloaderComponent],
    templateUrl: './current-price.component.html',
    styleUrl: './current-price.component.scss'
})
export class CurrentPriceComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  price = signal<number | null>(null);

  private apiService = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  constructor() {
    effect(() => {
      this.apiService.getInstrumentLastPrice(this.instrumentUid())
        .pipe(
          finalize(() => this.isLoaded.set(true)),
          takeUntilDestroyed(this.destroyRef),
        )
        .subscribe(price => this.price.set(price));
    });
  }

}
