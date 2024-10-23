import { Component, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AppService } from './app.service';
import { CommonModule } from '@angular/common';
import { InstrumentInList } from './types';
import { TableRowComponent } from './components/table-row/table-row.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, TableRowComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {

  instruments = signal<InstrumentInList[]>([]);

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstruments()
      .subscribe(resp => this.instruments.set(resp.filter((i, index) => index < 1000)));
  }

}
