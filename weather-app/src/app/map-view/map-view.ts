import {
  AfterViewInit,
  Component,
  DestroyRef,
  ElementRef,
  ViewChild,
  inject,
  OnDestroy,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';

import { StationUiStateService } from './map-station';
import { StationItem } from '../weather-api.service';

@Component({
  selector: 'app-map-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map-view.html',
  styleUrl: './map-view.css',
})
export class MapViewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('mapEl', { static: true }) mapEl!: ElementRef<HTMLDivElement>;
  @ViewChild('dragImage', { static: true }) dragImage!: ElementRef<HTMLImageElement>;

  private destroyRef = inject(DestroyRef);
  private map?: L.Map;

  private centerLayer = L.layerGroup();
  private stationsLayer = L.layerGroup();
  private dragPreviewLayer = L.layerGroup();

  constructor(private ui: StationUiStateService) {
    effect(() => {
      const center = this.ui.center();
      if (!this.map) return;
      if (!center) {
        this.centerLayer.clearLayers();
        return;
      }
      this.renderCenter(center.lat, center.lon, center.radius_km);
    });

    effect(() => {
      const stations = this.ui.stations();
      if (!this.map) return;
      this.renderStations(stations);
    });
  }

  private stationIcon = L.divIcon({
    className: 'station-pin',
    html: `<div class="pin"></div>`,
    iconSize: [28, 42],
    iconAnchor: [14, 42],
  });

  private centerIcon = L.divIcon({
    className: 'center-pin',
    html: `<div class="center-dot"></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });

  ngAfterViewInit(): void {
    const defaultCenter: L.LatLngExpression = [48.0636, 8.4597];

    this.map = L.map(this.mapEl.nativeElement, {
      zoomControl: false,
      attributionControl: true,
      minZoom: 3,
      maxBounds: [[-90, -180], [90, 180]],
      maxBoundsViscosity: 1.0
    }).setView(defaultCenter, 10);

    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
    }).addTo(this.map);

    this.centerLayer.addTo(this.map);
    this.stationsLayer.addTo(this.map);
    this.dragPreviewLayer.addTo(this.map);

    setTimeout(() => this.map?.invalidateSize(), 0);
  }

  private getRadiusFromZoom(): number {
    if (!this.map) return 30;

    const bounds = this.map.getBounds();
    const west = bounds.getWest();
    const east = bounds.getEast();
    const north = bounds.getNorth();
    const south = bounds.getSouth();
    const center = this.map.getCenter();

    const viewportWidth = L.latLng(center.lat, west).distanceTo(L.latLng(center.lat, east));
    const viewportHeight = L.latLng(south, center.lng).distanceTo(L.latLng(north, center.lng));

    const minDimMeters = Math.min(viewportWidth, viewportHeight);
    const radiusInKm = Math.round((minDimMeters / 1000) * 0.12);

    return Math.max(1, radiusInKm);
  }

  private renderCenter(lat: number, lon: number, radius_km?: number): void {
    this.centerLayer.clearLayers();
    const m = L.marker([lat, lon], { icon: this.centerIcon, interactive: false });
    m.addTo(this.centerLayer);

    if (radius_km) {
      const circle = L.circle([lat, lon], {
        radius: radius_km * 1000,
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.1,
        interactive: false,
      });
      circle.addTo(this.centerLayer);
    }
  }

  private renderStations(stations: StationItem[]): void {
    this.stationsLayer.clearLayers();

    for (const s of stations) {
      const m = L.marker([s.lat, s.lon], {
        icon: this.stationIcon,
        riseOnHover: true,
        keyboard: true,
        title: s.name,
      });

      m.on('click', () => {
        this.ui.openStation(s.station_id);
      });

      m.bindTooltip(s.name, {
        direction: 'top',
        offset: [0, -42],
        className: 'station-tooltip',
      });

      m.addTo(this.stationsLayer);
    }

    if (!this.map) return;

    const points: L.LatLng[] = [];

    this.stationsLayer.eachLayer((layer) => {
      const ll = (layer as any).getLatLng?.();
      if (ll) points.push(ll);
    });

    this.centerLayer.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        points.push(layer.getLatLng());
      } else if (layer instanceof L.Circle) {
        const circleBounds = layer.getBounds();
        points.push(circleBounds.getNorthEast());
        points.push(circleBounds.getSouthWest());
      }
    });

    if (points.length) {
      this.map.fitBounds(L.latLngBounds(points).pad(0.1));
    }
  }

  onDragStart(event: DragEvent): void {
    if (event.dataTransfer) {
      event.dataTransfer.setData('application/x-weather-pin', 'true');
      event.dataTransfer.effectAllowed = 'copyMove';

      if (this.dragImage?.nativeElement) {
        event.dataTransfer.setDragImage(this.dragImage.nativeElement, 24, 42);
      }
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    if (!this.map) return;
    event.dataTransfer!.dropEffect = 'copy';

    const rect = this.mapEl.nativeElement.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const latLng = this.map.containerPointToLatLng([x, y]);

    this.dragPreviewLayer.clearLayers();
    const radius_km = this.getRadiusFromZoom();

    L.circle(latLng, {
      radius: radius_km * 1000,
      color: '#3b82f6',
      dashArray: '5, 10',
      fillColor: '#3b82f6',
      fillOpacity: 0.1,
      interactive: false,
    }).addTo(this.dragPreviewLayer);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragPreviewLayer.clearLayers();

    if (!this.map) return;

    const isPin = event.dataTransfer?.getData('application/x-weather-pin');
    if (isPin !== 'true') return;

    const rect = this.mapEl.nativeElement.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const latLng = this.map.containerPointToLatLng([x, y]);
    const radius_km = this.getRadiusFromZoom();

    this.ui.setCenter(latLng.lat, latLng.lng, radius_km);
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = undefined;
  }
}
