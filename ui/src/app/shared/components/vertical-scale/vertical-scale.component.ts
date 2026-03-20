import { Component, input, computed } from '@angular/core';

@Component({
  selector: 'vertical-scale',
  standalone: true,
  templateUrl: './vertical-scale.component.html',
  styleUrl: './vertical-scale.component.scss'
})
export class VerticalScaleComponent {
  color = input.required<string>();
  value = input.required<number>();

  trackColor = computed(() => {
    return this.color() + '33';
  });

  fillHeight = computed(() => {
    const v = Math.max(0, Math.min(1, this.value()));
    return (v * 100) + '%';
  });
}
