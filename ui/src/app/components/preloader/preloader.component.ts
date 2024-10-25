import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';



@Component({
  selector: 'preloader',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './preloader.component.html',
  styleUrl: './preloader.component.scss'
})
export class PreloaderComponent {}
