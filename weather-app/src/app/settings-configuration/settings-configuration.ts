import { Component } from '@angular/core';
import { InputNumberModule } from 'primeng/inputnumber';
import { DatePickerModule } from 'primeng/datepicker';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { SelectModule } from 'primeng/select';

@Component({
  selector: 'app-settings-configuration',
  imports: [InputNumberModule, DatePickerModule, ButtonModule, CheckboxModule, SelectModule],
  templateUrl: './settings-configuration.html',
  styleUrl: './settings-configuration.css',
})
export class SettingsConfiguration {
  maxYearDate = new Date(2024, 11, 31);
  maxYearDateStart = new Date(2023, 11, 31);
  stations = [
    { name: 'New York'},
    { name: 'Los Angeles'},
    { name: 'Chicago'},
    { name: 'Houston'},
    { name: 'Phoenix'}
  ];
}
