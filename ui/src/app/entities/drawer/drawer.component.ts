import { Component, inject, model, resource } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonToggle, MatButtonToggleChange, MatButtonToggleGroup } from '@angular/material/button-toggle';
import { SortModeEnum } from '../../shared/types';
import { ApiService } from '../../shared/services/api.service';
import { firstValueFrom } from 'rxjs';


@Component({
  selector: 'drawer',
  imports: [CommonModule, MatButtonToggleGroup, MatButtonToggle],
  providers: [],
  templateUrl: './drawer.component.html',
  styleUrl: './drawer.component.scss'
})
export class DrawerComponent {

  sort = model<SortModeEnum>(SortModeEnum.BuyPerspective);

  sortModeEnum = SortModeEnum;

  isDrawerOpen = false;

  totalInfo = resource({
    loader: () => firstValueFrom(this._api.getTotalInfo()),
  });

  private _api = inject(ApiService);

  handleToggleDrawer(): void {
    this.isDrawerOpen = !this.isDrawerOpen;
  }

  handleChangeSort(e: MatButtonToggleChange): void {
    this.sort.set(e.value);
  }

}
