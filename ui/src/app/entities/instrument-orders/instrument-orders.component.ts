import { Component, inject, input, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { ApiService } from '../../shared/services/api.service';
import { ActiveOrder, BuyRecommendation, SellRecommendation } from '../../shared/types';
import { OrderCardComponent } from '../order-card/order-card.component';


@Component({
  selector: 'instrument-orders',
  imports: [
    CommonModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatIconModule,
    OrderCardComponent,
  ],
  templateUrl: './instrument-orders.component.html',
  styleUrl: './instrument-orders.component.scss',
})
export class InstrumentOrdersComponent implements OnInit {
  instrumentUid = input.required<string>();

  private apiService = inject(ApiService);

  buyRecommendation = signal<BuyRecommendation | null>(null);
  sellRecommendation = signal<SellRecommendation | null>(null);
  activeOrders = signal<ActiveOrder[]>([]);

  isBuyRecLoading = signal(false);
  isSellRecLoading = signal(false);
  isOrdersLoading = signal(false);

  activeOrdersBuy = computed(() =>
    this.activeOrders().filter(o => o.direction === 1)
  );

  activeOrdersSell = computed(() =>
    this.activeOrders().filter(o => o.direction === 2)
  );

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.loadBuyRecommendation();
    this.loadSellRecommendation();
    this.loadActiveOrders();
  }

  loadBuyRecommendation(): void {
    this.isBuyRecLoading.set(true);
    this.apiService.getBuyRecommendation(this.instrumentUid()).subscribe({
      next: (rec) => {
        this.buyRecommendation.set(rec);
        this.isBuyRecLoading.set(false);
      },
      error: () => this.isBuyRecLoading.set(false),
    });
  }

  loadSellRecommendation(): void {
    this.isSellRecLoading.set(true);
    this.apiService.getSellRecommendation(this.instrumentUid()).subscribe({
      next: (rec) => {
        this.sellRecommendation.set(rec);
        this.isSellRecLoading.set(false);
      },
      error: () => this.isSellRecLoading.set(false),
    });
  }

  loadActiveOrders(): void {
    this.isOrdersLoading.set(true);
    this.apiService.getInstrumentActiveOrders(this.instrumentUid()).subscribe({
      next: (orders) => {
        this.activeOrders.set(orders || []);
        this.isOrdersLoading.set(false);
      },
      error: () => this.isOrdersLoading.set(false),
    });
  }

  onOrderCreated(): void {
    setTimeout(() => this.loadActiveOrders(), 1500);
  }

  onOrderCancelled(): void {
    this.loadActiveOrders();
  }
}
