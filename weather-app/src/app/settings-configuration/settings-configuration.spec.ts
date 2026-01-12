import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SettingsConfiguration } from './settings-configuration';

describe('SettingsConfiguration', () => {
  let component: SettingsConfiguration;
  let fixture: ComponentFixture<SettingsConfiguration>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsConfiguration]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SettingsConfiguration);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
