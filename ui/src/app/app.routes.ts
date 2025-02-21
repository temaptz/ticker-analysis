import { Routes } from '@angular/router';
import { MainComponent } from './pages/main/main.component';
import { InstrumentComponent } from './pages/instrument/instrument.component';

export const routes: Routes = [
  { path: '', component: MainComponent },
  { path: 'instrument/:instrumentUid', component: InstrumentComponent },
];
