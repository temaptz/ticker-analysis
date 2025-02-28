import { Routes } from '@angular/router';
import { MainComponent } from './pages/main/main.component';
import { InstrumentComponent } from './pages/instrument/instrument.component';
import { ListComponent } from './pages/list/list.component';

export const routes: Routes = [

  {
    path: '',
    loadComponent: () => import('./pages/list/list.component').then(c => c.ListComponent)
  },
  {
    path: 'legacy',
    loadComponent: () => import('./pages/main/main.component').then(c => c.MainComponent)
  },
  {
    path: 'instrument/:instrumentUid',
    loadComponent: () => import('./pages/instrument/instrument.component').then(c => c.InstrumentComponent)
  },
];
