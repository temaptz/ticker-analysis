import { Component, input, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'weight-indicator',
  imports: [CommonModule],
  templateUrl: './weight-indicator.component.html',
  styleUrl: './weight-indicator.component.scss'
})
export class WeightIndicatorComponent {
  weight = input<number>(0);
  
  isLoading = input<boolean>(false);

  bgColor = computed(() => {
    const value = Math.min(Math.max(this.weight(), 0), 100);
    const alpha = value / 100;
    return `rgba(63, 81, 181, ${alpha.toFixed(2)})`;
  });

  displayStyle = computed(() => {
    const value = Math.min(Math.max(this.weight(), 0), 100);
    if (value === 0) {
      return 'rgba(63, 81, 181, 0.05)';
    }
    return this.bgColor();
  });
}
