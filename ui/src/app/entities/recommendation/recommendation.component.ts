import {
  Component,
  computed,
  DestroyRef,
  effect,
  inject,
  input,
  resource,
  ResourceLoaderParams,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize, firstValueFrom, forkJoin, lastValueFrom, map, of } from 'rxjs';
import { endOfDay, startOfDay, subDays } from 'date-fns';
import { ApiService } from '../../shared/services/api.service';
import { InstrumentInList, NewsListRatedResponse, RecommendationResp } from '../../shared/types';
import { PreloaderComponent } from '../preloader/preloader.component';
import { NewsBarComponent } from '../news-bar/news-bar.component';
import { RateV2Component } from '../rate-v2/rate-v2.component';


@Component({
  selector: 'recommendation',
  imports: [CommonModule, PreloaderComponent],
  providers: [],
  templateUrl: './recommendation.component.html',
  styleUrl: './recommendation.component.scss'
})
export class RecommendationComponent {

  instrumentUid = input.required<InstrumentInList['uid']>();
  isLong = input<boolean>(false);

  recommendationResource = resource<RecommendationResp, {uid: string, isLong: boolean}>({
    request: () => ({
      uid: this.instrumentUid(),
      isLong: this.isLong(),
    }),
    loader: (params: ResourceLoaderParams<{uid: string, isLong: boolean}>) => firstValueFrom(
      this.apiService.getInstrumentInvestRecommendation(params.request.uid, params.request.isLong),
    )
  });

  isRed = computed(() => this.recommendationResource?.value()?.short?.toLocaleLowerCase()?.includes('прода'));
  isGreen = computed(() => this.recommendationResource?.value()?.short?.toLocaleLowerCase()?.includes('покуп'));

  private apiService = inject(ApiService);

}
