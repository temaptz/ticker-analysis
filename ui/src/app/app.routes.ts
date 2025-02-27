import { Routes } from '@angular/router';
import { MainComponent } from './pages/main/main.component';
import { InstrumentComponent } from './pages/instrument/instrument.component';
import { ListComponent } from './pages/list/list.component';

export const routes: Routes = [
  { path: '', component: MainComponent },
  { path: 'list', component: ListComponent },
  { path: 'instrument/:instrumentUid', component: InstrumentComponent },
];
