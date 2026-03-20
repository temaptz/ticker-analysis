import { AfterViewInit, Component, ElementRef, input, OnChanges, output, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as echarts from 'echarts';


@Component({
  selector: 'echarts-graph',
  imports: [CommonModule],
  providers: [],
  templateUrl: './echarts-graph.component.html',
  styleUrl: './echarts-graph.component.scss'
})
export class EchartsGraphComponent implements AfterViewInit, OnChanges {

  option = input.required<echarts.EChartsOption>();
  width = input<string>('auto');
  height = input<string>('auto');

  onChartClick = output<Date>();

  private chart?: echarts.EChartsType;
  private isViewInit = false;

  @ViewChild('chart')
  private chartElRef?: ElementRef<HTMLDivElement>;

  ngAfterViewInit(): void {
    this.isViewInit = true;

    if (this.option()) {
      this.chart?.dispose();
      this.initChart();
    }

    window.addEventListener('resize', () => {
      this.chart?.resize();
    });
  }

  ngOnChanges(): void {
    if (this.isViewInit && this.option()) {
      this.chart?.dispose();
      this.initChart();
    }
  }

  private initChart(): void {
    this.chart = echarts.init(this.chartElRef?.nativeElement, null, { renderer: 'svg' });
    this.chart.setOption({
      animation: false,
      ...this.option(),
    });

    this.chart.on('click', (params) => {
      const date = (params as any)?.data?.[0] as Date;

      if (date) {
        this.onChartClick.emit(date);
      }
    });
  }

}

