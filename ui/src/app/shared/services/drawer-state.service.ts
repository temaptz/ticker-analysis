import { effect, Injectable, signal } from '@angular/core';


@Injectable({
  providedIn: 'root'
})
export class DrawerStateService {

  isOpen = signal<boolean>(false);

  constructor() {
    effect(() => {
      if (this.isOpen()) {
        document.body.classList.add('drawer-open');
      } else {
        document.body.classList.remove('drawer-open');
      }
    });
  }

  toggle(): void {
    this.isOpen.update(v => !v);
  }

}
