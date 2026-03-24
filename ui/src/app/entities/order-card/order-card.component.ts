import { Component, input, output, inject, signal, effect } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../shared/services/api.service';
import { AccountService } from '../../shared/services/account.service';
import { ActiveOrder, BuyRecommendation, SellRecommendation } from '../../shared/types';


@Component({
  selector: 'order-card',
  imports: [CommonModule, FormsModule, MatButtonModule, MatProgressSpinnerModule, MatTooltipModule, ReactiveFormsModule],
  providers: [DecimalPipe],
  templateUrl: './order-card.component.html',
  styleUrl: './order-card.component.scss',
})
export class OrderCardComponent {
  instrumentUid = input.required<string>();
  isBuy = input.required<boolean>();
  recommendation = input<BuyRecommendation | SellRecommendation | null>(null);
  activeOrder = input<ActiveOrder | null>(null);

  orderCreated = output<void>();
  orderCancelled = output<void>();

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  form = new FormGroup({
    price: new FormControl<number | null>(null, [Validators.required, Validators.min(0)]),
    qty: new FormControl<number | null>(null, [Validators.required, Validators.min(1)]),
  });

  private apiService = inject(ApiService);
  private accountService = inject(AccountService);

  constructor() {
    effect(() => {
      const rec = this.recommendation();
      if (rec) {
        this.form.setValue({
          price: this._round(rec.price_default),
          qty: rec.qty,
        });
      }
    });
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
    const price = Number(this.form.get('price')?.value);
    const qty = Number(this.form.get('qty')?.value);
    if (!price || !qty) return;
    this.isLoading.set(true);

    this.errorMessage.set(null);
    const accountId = this.accountService.selectedAccountId();
    this.apiService.createOrder({
      instrument_uid: this.instrumentUid(),
      quantity_lots: qty,
      price_rub: price,
      is_buy: this.isBuy(),
    }, accountId ?? undefined).subscribe({
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
    const accountId = this.accountService.selectedAccountId();
    this.apiService.cancelOrder(order.order_id, accountId ?? undefined).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.orderCancelled.emit();
      },
      error: () => this.isLoading.set(false),
    });
  }

  handleSetPrice(price: number | null | undefined): void {
    if (price) {
      this.form.get('price')?.setValue(this._round(price));
    }
  }

  private _round(num: number): number {
    return Math.round(num * 100) / 100;
  }
}
