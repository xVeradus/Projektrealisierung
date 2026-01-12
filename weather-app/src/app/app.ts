import { Component, signal } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { DataViewPage } from './data-view-page/data-view-page';

@Component({
  selector: 'app-root',
  imports: [ButtonModule, DataViewPage],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('angular19-primeng19-tailwind4');
}
