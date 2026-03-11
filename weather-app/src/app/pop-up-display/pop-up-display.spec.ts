import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PopUpDisplayComponent } from './pop-up-display';

describe('PopUpDisplayComponent', () => {
  let component: PopUpDisplayComponent;
  let fixture: ComponentFixture<PopUpDisplayComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PopUpDisplayComponent]
    })
      .compileComponents();

    fixture = TestBed.createComponent(PopUpDisplayComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
