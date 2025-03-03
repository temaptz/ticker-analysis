import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableFull2Component } from '../../widgets/table-full-2/table-full-2.component';


@Component({
  selector: 'list-2',
  imports: [CommonModule, TableFull2Component],
  providers: [],
  templateUrl: './list-2.component.html',
  styleUrl: './list-2.component.scss'
})
export class List2Component {
}
