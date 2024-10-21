import { Component, Input, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppService } from '../../app.service';
import { InstrumentHistoryPrice, InstrumentInList } from '../../types';
import { CandleInterval } from '../../enums';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';


@Component({
  selector: 'graph',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './graph.component.html',
  styleUrl: './graph.component.scss'
})
export class GraphComponent implements OnInit {

  @Input({required: true}) instrumentUid!: InstrumentInList['uid'];
  @Input({required: true}) days!: number;
  @Input({required: true}) interval!: CandleInterval;

  chartData = signal<ChartConfiguration<'line'>['data']>({
    datasets: [],
  });
  chartOptions: ChartConfiguration<'line'>['options'] = {
    plugins: {
      legend: {
        display: false
      }
    },
    elements: {
      line: {
        borderWidth: 1,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
      },
      point: {
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        radius: 1,
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        display: false
      },
      y: {
        grid: {
          display: false
        },
        display: false,
      }
    },
  };

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstrumentHistoryPrices(this.instrumentUid, this.days, this.interval)
      .subscribe((resp: InstrumentHistoryPrice[]) => {
        const chartData: ChartConfiguration<'line'>['data'] = {
          labels: resp.map(i => ''),
          datasets: [
            {
              data: resp.map(i => ((i.high + i.low) / 2)),
              tension: 0.1,
            }
          ]
        };
        this.chartData.set(chartData);
      });
  }

}
