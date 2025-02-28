import { Component, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ColDef } from 'ag-grid-community';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'column-visibility-switch',
  imports: [CommonModule, FormsModule],
  providers: [],
  templateUrl: './column-visibility-switch.component.html',
  styleUrl: './column-visibility-switch.component.scss'
})
export class ColumnVisibilitySwitchComponent {

  colDefs = input.required<ColDef[]>();

  onChangeHiddenFields = output<{colId: string, isVisible: boolean}>();

  isDialogOpen = signal<boolean>(false);

  toggleDialog(): void {
    this.isDialogOpen.set(!this.isDialogOpen());
  }

  handleChange(item: ColDef, isChecked: boolean): void {
    this.onChangeHiddenFields.emit({
      colId: item.colId!,
      isVisible: isChecked,
    });
  }

}
