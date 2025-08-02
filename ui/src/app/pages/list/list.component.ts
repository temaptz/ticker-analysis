import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableFull3Component } from '../../widgets/table-full-3/table-full-3.component';


@Component({
  selector: 'list',
  imports: [CommonModule, TableFull3Component],
  providers: [],
  templateUrl: './list.component.html',
  styleUrl: './list.component.scss'
})
export class ListComponent {
}
