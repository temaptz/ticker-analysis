import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableFullComponent } from '../../widgets/table-full/table-full.component';


@Component({
  selector: 'list',
  imports: [CommonModule, TableFullComponent],
  providers: [],
  templateUrl: './list.component.html',
  styleUrl: './list.component.scss'
})
export class ListComponent {
}
