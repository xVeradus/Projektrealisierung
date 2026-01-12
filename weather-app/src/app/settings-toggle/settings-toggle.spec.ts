import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SettingsToggle } from './settings-toggle';

describe('SettingsToggle', () => {
  let component: SettingsToggle;
  let fixture: ComponentFixture<SettingsToggle>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsToggle]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SettingsToggle);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
