import { Injectable, signal } from '@angular/core';
import { CandleInterval } from '../enums';
import { ComplexGraphControlOptions } from '../../entities/complex-graph-control/complex-graph-control.component';

const STORAGE_KEY = 'graph_control_settings';

const DEFAULT_SETTINGS: ComplexGraphControlOptions = {
  historyDaysCount: 90,
  interval: CandleInterval.CANDLE_INTERVAL_WEEK,
  futureDaysCount: 90,
  isShowNews: false,
  isShowTa_1_PredictionsHistory: false,
  isShowTa_1_1_PredictionsHistory: false,
  isShowTa_1_2_PredictionsHistory: false,
  isShowTa_2_PredictionsHistory: false,
  isShowTa_2_1_PredictionsHistory: false,
  isShowModels: false,
  isShowForecasts: false
};


@Injectable({
  providedIn: 'root'
})
export class GraphControlSettingsService {

  settings = signal<ComplexGraphControlOptions>(this.loadSettings());

  private loadSettings(): ComplexGraphControlOptions {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch (e) {
      console.error('Failed to load graph control settings from localStorage', e);
    }
    return { ...DEFAULT_SETTINGS };
  }

  private saveSettings(settings: ComplexGraphControlOptions): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) {
      console.error('Failed to save graph control settings to localStorage', e);
    }
  }

  updateSettings(settings: ComplexGraphControlOptions): void {
    this.settings.set(settings);
    this.saveSettings(settings);
  }

}
