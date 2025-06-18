import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/list-full/list-full.component').then(c => c.ListFullComponent)
  },
  {
    path: 'ticker/:ticker/fundamentals',
    loadComponent: () => import('./pages/fundamentals-page/fundamentals-page.component').then(c => c.FundamentalsPageComponent)
  },
  {
    path: 'ticker/:ticker',
    loadComponent: () => import('./pages/instrument/instrument.component').then(c => c.InstrumentComponent)
  },
];
