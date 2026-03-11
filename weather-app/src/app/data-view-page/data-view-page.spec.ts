import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DataViewPageComponent } from './data-view-page';

describe('DataViewPage', () => {
  let component: DataViewPageComponent;
  let fixture: ComponentFixture<DataViewPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataViewPageComponent]
    })
      .compileComponents();

    fixture = TestBed.createComponent(DataViewPageComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
