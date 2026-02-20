import { Component, input, output, inject, signal, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../shared/services/api.service';
import { ActiveOrder, BuyRecommendation, SellRecommendation } from '../../shared/types';


@Component({
  selector: 'order-card',
  imports: [CommonModule, FormsModule, MatButtonModule, MatProgressSpinnerModule, MatTooltipModule],
  providers: [DecimalPipe],
  templateUrl: './order-card.component.html',
  styleUrl: './order-card.component.scss',
})
export class OrderCardComponent implements OnChanges {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();
  recommendation = input<BuyRecommendation | SellRecommendation | null>(null);
  activeOrder = input<ActiveOrder | null>(null);

  orderCreated = output<void>();
  orderCancelled = output<void>();

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  editPrice = signal<number | null>(null);
  editQty = signal<number | null>(null);

  private initialized = false;
  private apiService = inject(ApiService);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['recommendation'] && !this.initialized) {
      const rec = this.recommendation();
      if (rec) {
        this.editPrice.set(rec.target_price);
        this.editQty.set(rec.qty);
        this.initialized = true;
      }
    }
  }

  get isBuyRec(): boolean {
    return this.isBuy();
  }

  get buyRec(): BuyRecommendation | null {
    const rec = this.recommendation();
    if (rec && 'total_price' in rec) return rec as BuyRecommendation;
    return null;
  }

  get sellRec(): SellRecommendation | null {
    const rec = this.recommendation();
    if (rec && !('total_price' in rec)) return rec as SellRecommendation;
    return null;
  }

  get order(): ActiveOrder | null {
    return this.activeOrder();
  }

  get isReal(): boolean {
    return !!this.order;
  }

  get directionLabel(): string {
    if (this.order) {
      return this.order.direction === 1 ? 'Покупка' : 'Продажа';
    }
    return this.isBuy() ? 'Покупка' : 'Продажа';
  }

  getMoneyValue(mv: any): number {
    if (!mv) return 0;
    return (mv.units || 0) + (mv.nano || 0) / 1e9;
  }

  createOrder(): void {
    const price = Number(this.editPrice());
    const qty = Number(this.editQty());
    if (!price || !qty) return;
    this.isLoading.set(true);

    this.errorMessage.set(null);
    this.apiService.createOrder({
      instrument_uid: this.instrumentUid(),
      quantity_lots: qty,
      price_rub: price,
      is_buy: this.isBuy(),
    }).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.orderCreated.emit();
      },
      error: (err) => {
        const detail = err?.error?.detail || err?.message || 'Неизвестная ошибка';
        this.errorMessage.set(detail);
        this.isLoading.set(false);
      },
    });
  }

  cancelOrder(): void {
    const order = this.order;
    if (!order) return;
    this.isLoading.set(true);
    this.apiService.cancelOrder(order.order_id).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.orderCancelled.emit();
      },
      error: () => this.isLoading.set(false),
    });
  }
}
