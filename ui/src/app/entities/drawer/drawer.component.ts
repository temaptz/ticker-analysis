import { Component, model } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonToggle, MatButtonToggleChange, MatButtonToggleGroup } from '@angular/material/button-toggle';
import { SortModeEnum } from '../../shared/types';


@Component({
  selector: 'drawer',
  imports: [CommonModule, MatButtonToggleGroup, MatButtonToggle],
  providers: [],
  templateUrl: './drawer.component.html',
  styleUrl: './drawer.component.scss'
})
export class DrawerComponent {

  sort = model<SortModeEnum>(SortModeEnum.PotentialPerspective);

  sortModeEnum = SortModeEnum;

  isDrawerOpen = false;

  handleToggleDrawer(): void {
    this.isDrawerOpen = !this.isDrawerOpen;
  }

  handleChangeSort(e: MatButtonToggleChange): void {
    this.sort.set(e.value);
  }

}
