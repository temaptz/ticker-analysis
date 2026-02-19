import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom, map } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { BuySellTotalRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'total-rate',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './total-rate.component.html',
  styleUrl: './total-rate.component.scss'
})
export class TotalRateComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  totalColor = GRAPH_COLORS.total_rate;

  rateData = resource<BuySellTotalRateResp, { uid: string, isBuy: boolean }>({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string, isBuy: boolean }>) => firstValueFrom(
      this.apiService.getBuySellTotalRate(
        params.request.uid,
        params.request.isBuy
      )
    )
  });

  getTooltip(data: BuySellTotalRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
