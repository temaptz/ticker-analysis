import { Component, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AppService } from './app.service';
import { CommonModule } from '@angular/common';
import { Instrument } from './types';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {

  instruments = signal<Instrument[]>([]);

  constructor(
    private appService: AppService,
  ) {}

  ngOnInit() {
    this.appService.getInstruments()
      .subscribe(resp => this.instruments.set(resp));
  }

}
