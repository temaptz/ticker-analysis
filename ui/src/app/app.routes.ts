import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/list/list.component').then(c => c.ListComponent)
  },
  {
    path: 'instrument/:instrumentUid',
    loadComponent: () => import('./pages/instrument/instrument.component').then(c => c.InstrumentComponent)
  },
];
