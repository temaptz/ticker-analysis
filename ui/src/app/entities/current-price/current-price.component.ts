import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
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

  constructor(
    private appService: ApiService,
  ) {
    effect(() => {
      this.appService.getInstrumentLastPrice(this.instrumentUid())
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe(price => this.price.set(price));
    });
  }

}
