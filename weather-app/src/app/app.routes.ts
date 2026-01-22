import { Routes } from '@angular/router';
import { DataViewPageComponent } from '../app/data-view-page/data-view-page';

export const routes: Routes = [
  { path: '', component: DataViewPageComponent },
  { path: '**', redirectTo: '' },
];
