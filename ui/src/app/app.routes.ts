import { Routes } from '@angular/router';
import { MainComponent } from './pages/main/main.component';
import { NewsPageComponent } from './pages/news-page/news-page.component';

export const routes: Routes = [
  { path: '', component: MainComponent },
  { path: 'news/:instrumentUid', component: NewsPageComponent },
];
