import { inject, Injectable } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { addHours, startOfDay } from 'date-fns';
import { AppService } from './app.service';


@Injectable({
  providedIn: 'root'
})
export class CurrentPriceService {

  private observablesMap = new Map<string, Observable<number | null>>();
  private todayMidDay: Date = addHours(startOfDay(new Date()), 12);

  private _api = inject(AppService);

  getPriceByUid(uid: string): Observable<number | null> {
    if (!this.observablesMap.has(uid)) {
      this.observablesMap.set(
        uid,
        this._api.getInstrumentPriceByDate(uid, this.todayMidDay)
          .pipe(
            shareReplay({ bufferSize: 1, refCount: true }),
          )
      );
    }

    return this.observablesMap.get(uid)!;
  }

}
