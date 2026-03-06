import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom, map } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { BuySellTotalRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';
import { AccountService } from '../../../../shared/services/account.service';

@Component({
  selector: 'total',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './total.component.html',
  styleUrl: './total.component.scss'
})
export class TotalComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  accountService = inject(AccountService);
  decimalPipe = inject(DecimalPipe);

  totalColor = GRAPH_COLORS.total_rate;

  rateData = resource<BuySellTotalRateResp, { uid: string, accountId: number, isBuy: boolean }>({
    request: () => ({ uid: this.instrumentUid(), accountId: this.accountService.selectedAccountId() ?? 0, isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string, accountId: number, isBuy: boolean }>) => firstValueFrom(
      this.apiService.getBuySellTotalRate(
        params.request.uid,
        params.request.accountId,
        params.request.isBuy
      )
    )
  });

  getTooltip(data: BuySellTotalRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
