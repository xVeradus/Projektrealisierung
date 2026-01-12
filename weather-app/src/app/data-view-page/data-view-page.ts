import { Component } from '@angular/core';
import { Graph } from '../graph/graph';
import { Settings } from '../settings/settings';
import { Table } from '../table/table';

@Component({
  selector: 'app-data-view-page',
  imports: [Graph, Settings, Table],
  templateUrl: './data-view-page.html',
  styleUrl: './data-view-page.css',
})
export class DataViewPage {

}
