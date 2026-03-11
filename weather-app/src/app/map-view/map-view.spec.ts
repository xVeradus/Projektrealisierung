import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MapViewComponent } from './map-view';

describe('MapView', () => {
  let component: MapViewComponent;
  let fixture: ComponentFixture<MapViewComponent>;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapViewComponent]
    })
      .compileComponents();

    fixture = TestBed.createComponent(MapViewComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
