import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ToggleSwitchModule } from 'primeng/toggleswitch';

@Component({
  selector: 'app-settings-toggle',
  imports: [FormsModule, ToggleSwitchModule],
  templateUrl: './settings-toggle.html',
  styleUrl: './settings-toggle.css',
})
export class SettingsToggle {
  checkedLegend = false;
  checkedDark = false;
  checkedMap = false;
}
