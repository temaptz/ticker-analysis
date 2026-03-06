import { Component, computed, inject, model, resource } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { SortModeEnum } from '../../shared/types';
import { ApiService } from '../../shared/services/api.service';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { GraphControlSettingsService } from '../../shared/services/graph-control-settings.service';
import { DrawerStateService } from '../../shared/services/drawer-state.service';
import { AccountService } from '../../shared/services/account.service';
import { ComplexGraphControlComponent, ComplexGraphControlOptions } from '../complex-graph-control/complex-graph-control.component';
import { WeightsEditorComponent } from '../weights-editor/weights-editor.component';
import { AccountSwitchComponent } from '../account-switch/account-switch.component';


@Component({
  selector: 'drawer',
  imports: [CommonModule, FormsModule, ComplexGraphControlComponent, WeightsEditorComponent, AccountSwitchComponent],
  providers: [],
  templateUrl: './drawer.component.html',
  styleUrl: './drawer.component.scss'
})
export class DrawerComponent {

  sortModeEnum = SortModeEnum;

  private _drawerStateService = inject(DrawerStateService);
  private _accountService = inject(AccountService);

  isDrawerOpen = this._drawerStateService.isOpen;

  accounts = this._accountService.accounts;

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
    this._drawerStateService.toggle();
  }

  setSort(mode: SortModeEnum): void {
    this.sort.set(mode);
    this._sortModeService.setSortMode(mode);
  }

  handleChangeGraphSettings(options: ComplexGraphControlOptions): void {
    this._graphControlSettingsService.updateSettings(options);
  }

}
