import { Component, effect, inject, resource, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentLogoComponent } from '../instrument-logo/instrument-logo.component';
import { InstrumentInList, SortModeEnum } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { SortModeService } from '../../shared/services/sort-mode.service';
import { AccountService } from '../../shared/services/account.service';

@Component({
  selector: 'instrument-select',
  imports: [CommonModule, MatSelectModule, MatFormFieldModule, FormsModule, ReactiveFormsModule, InstrumentLogoComponent, PreloaderComponent],
  templateUrl: './instrument-select.component.html',
  styleUrl: './instrument-select.component.scss'
})
export class InstrumentSelectComponent {
  private apiService = inject(ApiService);
  private sortModeService = inject(SortModeService);
  private accountService = inject(AccountService);

  selectedInstrument = signal<InstrumentInList | null>(null);
  selectControl = new FormControl<string>('');

  instrumentsResource = resource<InstrumentInList[], {sort: number, accountId: number | null}>({
    defaultValue: [],
    params: () => ({
      sort: this.sortModeService.sortMode() ?? SortModeEnum.BuyPerspective,
      accountId: this.accountService.selectedAccountId() ?? null,
    }),
    loader: (params): Promise<InstrumentInList[]> => {
      if (!params?.params?.accountId) {
        return Promise.resolve([]);
      }
      return firstValueFrom(this.apiService.getInstruments(params.params.accountId));
    }
  });

  constructor() {
    effect(() => {
      const instruments = this.instrumentsResource.value();
      if (instruments?.length && !this.selectedInstrument()) {
        this.selectedInstrument.set(instruments[0]);
        this.selectControl.setValue(instruments[0].uid);
      }
    });
  }

  onSelectionChange(uid: string): void {
    const instruments = this.instrumentsResource.value();
    const found = instruments?.find((i: InstrumentInList) => i.uid === uid);
    if (found) {
      this.selectedInstrument.set(found);
    }
  }
}
