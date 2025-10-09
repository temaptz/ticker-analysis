import { Routes } from '@angular/router';
import { authGuard } from './shared/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full',
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(c => c.LoginComponent),
    canDeactivate: [authGuard]
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/list/list.component').then(c => c.ListComponent),
    canActivate: [authGuard]
  },
  {
    path: 'full',
    loadComponent: () => import('./pages/list-full/list-full.component').then(c => c.ListFullComponent),
    canActivate: [authGuard]
  },
  {
    path: 'ticker/:ticker/fundamentals',
    loadComponent: () => import('./pages/fundamentals-page/fundamentals-page.component').then(c => c.FundamentalsPageComponent),
    canActivate: [authGuard]
  },
  {
    path: 'ticker/:ticker',
    loadComponent: () => import('./pages/instrument/instrument.component').then(c => c.InstrumentComponent),
    canActivate: [authGuard]
  },
];
