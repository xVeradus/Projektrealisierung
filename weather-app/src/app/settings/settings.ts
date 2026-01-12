import { Component } from '@angular/core';
import { SettingsConfiguration } from '../settings-configuration/settings-configuration';
import { SettingsFilter } from '../settings-filter/settings-filter';
import { SettingsToggle } from '../settings-toggle/settings-toggle';

@Component({
  selector: 'app-settings',
  imports: [SettingsConfiguration, SettingsFilter, SettingsToggle],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings {

}
