import { Component, computed, input, output, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatSliderModule } from '@angular/material/slider';
import { format } from 'date-fns';

@Component({
  selector: 'date-timeline',
  imports: [CommonModule, MatSliderModule, FormsModule],
  templateUrl: './date-timeline.component.html',
  styleUrl: './date-timeline.component.scss'
})
export class DateTimelineComponent {
  startDate = input.required<Date>();
  endDate = input.required<Date>();
  
  selectedDateChange = output<Date>();
  
  minTimestamp = computed(() => this.startDate().getTime());
  maxTimestamp = computed(() => this.endDate().getTime());
  
  sliderValue = signal<number>(0);
  
  // Шаг в 1 день (в миллисекундах)
  readonly dayStep = 24 * 60 * 60 * 1000;

  constructor() {
    effect(() => {
      const start = this.startDate();
      if (start && this.sliderValue() === 0) {
        this.sliderValue.set(start.getTime());
      }
    });
  }
  
  onInputChange(): void {
    const value = this.sliderValue();
    this.selectedDateChange.emit(new Date(value));
  }
  
  // Форматирование даты для отображения на ползунке
  formatDateLabel = (value: number): string => {
    return format(new Date(value), 'dd.MM.yy');
  };
  
  // Получение текущей выбранной даты
  selectedDate = computed(() => new Date(this.sliderValue()));
}
