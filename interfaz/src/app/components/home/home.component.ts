import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  leftLampState: any;
  rightLampState: any;
  readingLampState: any;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadAllLampStates();
  }

  // ✅ Cargar estados de todas las lámparas
  loadAllLampStates(): void {
    this.apiService.getLeftLampState().subscribe(response => {
      this.leftLampState = response;
    });

    this.apiService.getRightLampState().subscribe(response => {
      this.rightLampState = response;
    });

    this.apiService.getReadingLampState().subscribe(response => {
      this.readingLampState = response;
    });
  }

  // ✅ Control de la lámpara izquierda
  turnOnLeftLamp(): void {
    this.apiService.turnOnLeftLamp().subscribe(response => {
      console.log('Lámpara izquierda encendida:', response);
      this.loadAllLampStates();
    });
  }

  turnOffLeftLamp(): void {
    this.apiService.turnOffLeftLamp().subscribe(response => {
      console.log('Lámpara izquierda apagada:', response);
      this.loadAllLampStates();
    });
  }

  // ✅ Control de la lámpara derecha
  turnOnRightLamp(): void {
    this.apiService.turnOnRightLamp().subscribe(response => {
      console.log('Lámpara derecha encendida:', response);
      this.loadAllLampStates();
    });
  }

  turnOffRightLamp(): void {
    this.apiService.turnOffRightLamp().subscribe(response => {
      console.log('Lámpara derecha apagada:', response);
      this.loadAllLampStates();
    });
  }

  // ✅ Control de la luz de lectura
  turnOnReadingLamp(): void {
    this.apiService.turnOnReadingLamp().subscribe(response => {
      console.log('Lámpara de lectura encendida:', response);
      this.loadAllLampStates();
    });
  }

  turnOffReadingLamp(): void {
    this.apiService.turnOffReadingLamp().subscribe(response => {
      console.log('Lámpara de lectura apagada:', response);
      this.loadAllLampStates();
    });
  }
}
