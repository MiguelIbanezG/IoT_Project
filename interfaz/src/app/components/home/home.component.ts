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
  cameraStreamUrl: string = '';
  private partyModeInterval: any = null;
  private alertModeInterval: any = null;
  partyModeActive: boolean = false;
  alertModeActive: boolean = false;
  warmModeActive: boolean = false;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadAllLampStates();
    this.cameraStreamUrl = this.apiService.getCameraStream();
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

  startPartyMode(): void {
    if (this.partyModeInterval) return;

    this.partyModeActive = true;
    const temperatures = [1800, 2700, 4000, 5000, 6500];
    const colors = [
      [255, 0, 0],
      [0, 255, 0],
      [0, 0, 255],
      [255, 255, 0],
      [255, 0, 255]
    ];

    let index = 0;
    this.partyModeInterval = setInterval(() => {
      this.apiService.setLampTemperature('light.lampara_izquierda', temperatures[index % temperatures.length]).subscribe();
      this.apiService.setLampTemperature('light.lampara_de_lectura', temperatures[index % temperatures.length]).subscribe();
      this.apiService.setLampColor('light.lampara_derecha', colors[index % colors.length]).subscribe();
      index++;
    }, 500);
  }

  stopPartyMode(): void {
    if (this.partyModeInterval) {
      clearInterval(this.partyModeInterval);
      this.partyModeInterval = null;
      this.partyModeActive = false;
    }
    this.turnOffLeftLamp();
    this.turnOffRightLamp();
    this.turnOffReadingLamp();
  }

  startAlertMode(): void {
    if (this.alertModeInterval) return;

    this.alertModeActive = true;
    let isOn = false;

    this.alertModeInterval = setInterval(() => {
      if (isOn) {
        this.apiService.setLampTemperature('light.lampara_izquierda', 1800).subscribe();
        this.apiService.setLampTemperature('light.lampara_de_lectura', 1800).subscribe();
        this.apiService.setLampColor('light.lampara_derecha', [255, 0, 0]).subscribe();
      } else {
        this.apiService.turnOffLeftLamp().subscribe();
        this.apiService.turnOffRightLamp().subscribe();
        this.apiService.turnOffReadingLamp().subscribe();
      }
      isOn = !isOn;
    }, 500);
  }

  stopAlertMode(): void {
    if (this.alertModeInterval) {
      clearInterval(this.alertModeInterval);
      this.alertModeInterval = null;
      this.alertModeActive = false;
    }
    this.turnOffLeftLamp();
    this.turnOffRightLamp();
    this.turnOffReadingLamp();
  }

  startWarmMode(): void {
    this.apiService.setLampTemperature('light.lampara_izquierda', 2200).subscribe();
    this.apiService.setLampColor('light.lampara_derecha', [255, 140, 0]).subscribe();
    this.warmModeActive = true;
  }

  stopWarmMode(): void {
    this.apiService.turnOffLeftLamp().subscribe();
    this.apiService.turnOffRightLamp().subscribe();
    this.warmModeActive = false;
  }

}
