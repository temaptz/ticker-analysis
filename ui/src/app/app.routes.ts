import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/list-2/list-2.component').then(c => c.List2Component)
  },
  {
    path: 'list', // @DEPRECATED
    loadComponent: () => import('./pages/list/list.component').then(c => c.ListComponent)
  },
  {
    path: 'legacy', // @DEPRECATED
    loadComponent: () => import('./pages/main/main.component').then(c => c.MainComponent)
  },
  {
    path: 'instrument/:instrumentUid',
    loadComponent: () => import('./pages/instrument/instrument.component').then(c => c.InstrumentComponent)
  },
];
