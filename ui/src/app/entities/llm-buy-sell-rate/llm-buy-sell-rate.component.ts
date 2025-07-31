import { Component, inject, input, resource, ResourceLoaderParams } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { ApiService } from '../../shared/services/api.service';


@Component({
    selector: 'llm-buy-sell-rate',
    imports: [CommonModule],
    providers: [DecimalPipe],
    templateUrl: './llm-buy-sell-rate.component.html',
    styleUrl: './llm-buy-sell-rate.component.scss'
})
export class LlmBuySellRateComponent {

  instrumentUid = input.required<string>()

  buy = resource<string, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.apiService.getInstrumentTag(params.request, 'llm_buy_rate'),
    )
  });

  buyConclusion = resource<string, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.apiService.getInstrumentTag(params.request, 'llm_buy_conclusion'),
    )
  });

  sell = resource<string, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.apiService.getInstrumentTag(params.request, 'llm_sell_rate'),
    )
  });

  sellConclusion = resource<string, string>({
    request: () => this.instrumentUid(),
    loader: (params: ResourceLoaderParams<string>) => firstValueFrom(
      this.apiService.getInstrumentTag(params.request, 'llm_sell_conclusion'),
    )
  });

  apiService = inject(ApiService);

}
