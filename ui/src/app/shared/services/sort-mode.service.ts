import { Injectable, signal } from '@angular/core';
import { SortModeEnum } from '../types';


@Injectable({
  providedIn: 'root'
})
export class SortModeService {

  sortMode = signal<SortModeEnum>(SortModeEnum.BuyPerspective);

  setSortMode(mode: SortModeEnum): void {
    this.sortMode.set(mode);
  }

}
