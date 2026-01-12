import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DataViewPage } from './data-view-page';

describe('DataViewPage', () => {
  let component: DataViewPage;
  let fixture: ComponentFixture<DataViewPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataViewPage]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DataViewPage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
