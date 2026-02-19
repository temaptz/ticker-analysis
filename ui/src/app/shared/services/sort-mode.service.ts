import { Injectable, signal } from '@angular/core';
import { SortModeEnum } from '../types';


@Injectable({
  providedIn: 'root'
})
export class SortModeService {

  private readonly lsKey = 'sortTickers';

  sortMode = signal<SortModeEnum>(this.loadSortMode());

  setSortMode(mode: SortModeEnum): void {
    this.sortMode.set(mode);
    this.saveSortMode(mode);
  }

  private loadSortMode(): SortModeEnum {
    try {
      const stored = localStorage.getItem(this.lsKey);
      if (stored) {
        return JSON.parse(stored) ?? SortModeEnum.BuyPerspective;
      }
    } catch (e) {
      // ignore
    }
    return SortModeEnum.BuyPerspective;
  }

  private saveSortMode(mode: SortModeEnum): void {
    try {
      localStorage.setItem(this.lsKey, JSON.stringify(mode));
    } catch (e) {
      // ignore
    }
  }

}
