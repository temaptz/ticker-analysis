import { Component, computed, inject, model, resource } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonToggle, MatButtonToggleChange, MatButtonToggleGroup } from '@angular/material/button-toggle';
import { firstValueFrom } from 'rxjs';
import { SortModeEnum } from '../../shared/types';
import { ApiService } from '../../shared/services/api.service';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { GraphControlSettingsService } from '../../shared/services/graph-control-settings.service';
import { ComplexGraphControlComponent, ComplexGraphControlOptions } from '../complex-graph-control/complex-graph-control.component';


@Component({
  selector: 'drawer',
  imports: [CommonModule, MatButtonToggleGroup, MatButtonToggle, ComplexGraphControlComponent],
  providers: [],
  templateUrl: './drawer.component.html',
  styleUrl: './drawer.component.scss'
})
export class DrawerComponent {

  sortModeEnum = SortModeEnum;

  isDrawerOpen = false;

  totalInfo = resource({
    loader: () => firstValueFrom(this._api.getTotalInfo()),
  });

  weekPercent = computed<number>(() => {
    const info = this.totalInfo.value();

    if (info) {
      return Math.round(info.news_week_rated_count / info.news_week_count * 100);
    }

    return 0;
  });

  monthPercent = computed<number>(() => {
    const info = this.totalInfo.value();

    if (info) {
      return Math.round(info.news_month_rated_count / info.news_month_count * 100);
    }

    return 0;
  });

  totalPercent = computed<number>(() => {
    const info = this.totalInfo.value();

    if (info) {
      return Math.round(info.news_total_rated_count / info.news_total_count * 100);
    }

    return 0;
  });

  private _api = inject(ApiService);
  private _sortModeService = inject(SortModeService);
  private _graphControlSettingsService = inject(GraphControlSettingsService);

  sort = model<SortModeEnum>(this._sortModeService.sortMode());
  graphSettings = this._graphControlSettingsService.settings;

  handleToggleDrawer(): void {
    this.isDrawerOpen = !this.isDrawerOpen;
  }

  handleChangeSort(e: MatButtonToggleChange): void {
    this.sort.set(e.value);
    this._sortModeService.setSortMode(e.value);
  }

  handleChangeGraphSettings(options: ComplexGraphControlOptions): void {
    this._graphControlSettingsService.updateSettings(options);
  }

}
