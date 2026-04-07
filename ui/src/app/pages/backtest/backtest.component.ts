import { Component, ViewChild, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { addDays, subDays } from 'date-fns';
import { InstrumentSelectComponent } from '../../entities/instrument-select/instrument-select.component';
import { BacktestGraphComponent } from '../../entities/backtest-graph/backtest-graph.component';
import { BuySellRateComponent } from '../../entities/buy-sell-rate/buy-sell-rate.component';
import { DrawerComponent } from '../../entities/drawer/drawer.component';
import { AccountService } from '../../shared/services/account.service';

@Component({
  selector: 'backtest',
  imports: [
    CommonModule,
    InstrumentSelectComponent,
    BacktestGraphComponent,
    BuySellRateComponent,
    DrawerComponent,
  ],
  templateUrl: './backtest.component.html',
  styleUrl: './backtest.component.scss'
})
export class BacktestComponent {
  @ViewChild('instrumentSelect') instrumentSelect!: InstrumentSelectComponent;

  private accountService = inject(AccountService);

  selectedPeriod = signal<number>(1);
  selectedDate = signal<Date>(subDays(new Date(), 30));

  periodOptions = [
    { label: '1г', value: 1 },
    { label: '3г', value: 3 },
    { label: '5г', value: 5 },
    { label: '10л', value: 10 },
  ];

  accountId = computed(() => this.accountService.selectedAccountId());

  onSelectPeriod(years: number): void {
    this.selectedPeriod.set(years);
    this.selectedDate.set(subDays(new Date(), years * 365));
  }

  onGraphClick(date: Date): void {
    this.selectedDate.set(date);
  }

  handlePrevDay(): void {
    this.selectedDate.update((date) => subDays(date, 1));
  }

  handleNextDay(): void {
    this.selectedDate.update((date) => addDays(date, 1));
  }
}
