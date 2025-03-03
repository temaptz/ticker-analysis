import { inject, Pipe, PipeTransform } from '@angular/core';
import { Observable, of } from 'rxjs';
import { CurrentPriceService } from '../services/current-price.service';

@Pipe({
  name: 'currentPriceByUid',
  standalone: true
})
export class CurrentPriceByUidPipe implements PipeTransform {

  private currentPriceService = inject(CurrentPriceService);

  transform(instrument_uid: string): Observable<number | null> {
    try {
      return this.currentPriceService.getPriceByUid(instrument_uid);
    } catch (e) {
      console.error('Error CurrentPriceByUidPipe transform', (e as any)?.message ?? e);

      return of(null);
    }
  }

}
