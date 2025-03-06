import { inject, Injectable } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { addHours, isAfter, isBefore, startOfDay, startOfHour } from 'date-fns';
import { ApiService } from './api.service';


@Injectable({
  providedIn: 'root'
})
export class CurrentPriceService {

  private observablesMap = new Map<string, Observable<number | null>>();
  private todayStartDay: Date = addHours(startOfDay(new Date()), 9);
  private todayEndDay: Date = addHours(startOfDay(new Date()), 18);

  private _api = inject(ApiService);

  getPriceByUid(uid: string): Observable<number | null> {
    let date = startOfHour(new Date());
    date = isAfter(date, this.todayStartDay) ? date : this.todayStartDay;
    date = isBefore(date, this.todayEndDay) ? date : this.todayEndDay;

    if (!this.observablesMap.has(uid)) {
      this.observablesMap.set(
        uid,
        this._api.getInstrumentPriceByDate(uid, date)
          .pipe(
            shareReplay({ bufferSize: 1, refCount: true }),
          )
      );
    }

    return this.observablesMap.get(uid)!;
  }

}
