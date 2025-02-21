import { Component, effect, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs';
import { parseJSON } from 'date-fns';
import { AppService } from '../../app.service';
import { InstrumentInList } from '../../types';
import { getPriceByQuotation } from '../../utils';
import { PreloaderComponent } from '../preloader/preloader.component';


@Component({
  selector: 'current-price',
  standalone: true,
  imports: [CommonModule, PreloaderComponent],
  templateUrl: './current-price.component.html',
  styleUrl: './current-price.component.scss'
})
export class CurrentPriceComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();

  isLoaded = signal<boolean>(false);
  price = signal<number | null>(null);

  constructor(
    private appService: AppService,
  ) {
    effect(() => {
      this.appService.getInstrumentLastPrices(this.instrumentUid())
        .pipe(finalize(() => this.isLoaded.set(true)))
        .subscribe(resp => {
          const price = resp
            ?.sort((a, b) => parseJSON(a.time).getTime() - parseJSON(b.time).getTime())
            ?.[0];

          const nextPrice = getPriceByQuotation(price.price);

          this.price.set(nextPrice);
        });
    }, { allowSignalWrites: true });
  }

}
