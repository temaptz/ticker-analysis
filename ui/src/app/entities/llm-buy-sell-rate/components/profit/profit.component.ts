import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { MatTooltip } from '@angular/material/tooltip';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../../../shared/services/api.service';
import { ProfitRateResp } from '../../../../shared/types';
import { GRAPH_COLORS } from '../../../../shared/const';
import { VerticalScaleComponent } from '../vertical-scale/vertical-scale.component';

@Component({
  selector: 'profit',
  imports: [CommonModule, MatTooltip, VerticalScaleComponent],
  providers: [DecimalPipe],
  templateUrl: './profit.component.html',
  styleUrl: './profit.component.scss'
})
export class ProfitComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();

  apiService = inject(ApiService);
  decimalPipe = inject(DecimalPipe);

  profitColor = GRAPH_COLORS.profit_rate;

  rateData = resource({
    request: () => ({ uid: this.instrumentUid(), isBuy: this.isBuy() }),
    loader: (params: ResourceLoaderParams<{ uid: string; isBuy: boolean }>) =>
      firstValueFrom(this.apiService.getInstrumentProfitRate(params.request.uid, params.request.isBuy))
  });

  getTooltip(data: ProfitRateResp): string {
    return JSON.stringify(data.debug, null, 2);
  }
}
