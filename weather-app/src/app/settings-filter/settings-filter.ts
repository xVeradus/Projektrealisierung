import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CheckboxModule } from 'primeng/checkbox';

@Component({
  selector: 'app-settings-filter',
  imports: [FormsModule, CheckboxModule],
  templateUrl: './settings-filter.html',
  styleUrl: './settings-filter.css',
})
export class SettingsFilter {
  checkedTminYear = false;
  checkedTmaxYear = false;
  checkedTminSpring = false;
  checkedTmaxSpring = false;
  checkedTminSummer = false;
  checkedTmaxSummer = false;
  checkedTminAutumn = false;
  checkedTmaxAutumn = false;
  checkedTminWinter = false;
  checkedTmaxWinter = false;
}