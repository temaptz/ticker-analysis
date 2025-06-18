import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableFullComponent } from '../../widgets/table-full/table-full.component';


@Component({
  selector: 'list-full',
  imports: [CommonModule, TableFullComponent],
  providers: [],
  templateUrl: './list-full.component.html',
  styleUrl: './list-full.component.scss'
})
export class ListFullComponent {
}
