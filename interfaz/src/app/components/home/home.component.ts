import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  leftLampState: any;
  rightLampState: any;
  photoUrl: SafeUrl | null = null;
  readingLampState: any;
  private partyModeInterval: any = null;
  private alertModeInterval: any = null;
  partyModeActive: boolean = false;
  alertModeActive: boolean = false;
  warmModeActive: boolean = false;
  cameraStreamUrl: string = "http://master:master@150.244.57.136/axis-cgi/mjpg/video.cgi?resolution=640x480";
  videoStreamUrl: string = 'http://localhost:5000/video_feed';  // URL del backend de video
  showPhoto: boolean = true;
  isListening = false;
  recognition: any;

  
  constructor(private apiService: ApiService, private sanitizer: DomSanitizer) {}

  ngOnInit(): void {
    this.loadAllLampStates();
  }

  openCamera(): void {
    const cameraUrl = "http://master:master@150.244.57.136/axis-cgi/mjpg/video.cgi?resolution=640x480";
    window.open(cameraUrl, "_blank");
  }

  captureImage(): void {
    this.apiService.getImage().subscribe(blob => {
      const objectURL = URL.createObjectURL(blob);
      this.photoUrl = this.sanitizer.bypassSecurityTrustUrl(objectURL);
    }, error => {
      console.error("Error al capturar la imagen:", error);
    });
  }

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
        this.turnOffAllLamps();
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
    this.turnOffAllLamps();
  }

  startWarmMode(): void {
    this.apiService.setLampTemperature('light.lampara_izquierda', 2200).subscribe();
    this.apiService.setLampColor('light.lampara_derecha', [255, 140, 0]).subscribe();
    this.apiService.setLampTemperature('light.lampara_de_lectura', 2200).subscribe();
    this.warmModeActive = true;
  }

  stopWarmMode(): void {
    this.turnOffAllLamps();
    this.warmModeActive = false;
  }

  turnOffAllLamps(): void {
    this.turnOffLeftLamp();
    this.turnOffRightLamp();
    this.turnOffReadingLamp();
  }

  closePhoto() {
    this.showPhoto = false;
  }

  handleVoiceCommand(command: string): void {
    command = command.toLowerCase().trim();
  
    // === Lámparas por temperatura ===
    const temperaturaMap: { [key: string]: number } = {
      'frío': 6500,
      'normal': 4000,
      'cálido': 1800,
      'calido': 1800
    };
  
    for (const [ambiente, temp] of Object.entries(temperaturaMap)) {
      if (command.includes(`encender lectura ${ambiente}`)) {
        this.apiService.setLampTemperature('light.lampara_de_lectura', temp).subscribe(() => {
          console.log(`Lámpara de lectura encendida con temperatura ${ambiente} (${temp}K)`);
        });
        return;
      }
  
      if (command.includes(`encender luz izquierda ${ambiente}`) || command.includes(`encender lámpara izquierda ${ambiente}`)) {
        this.apiService.setLampTemperature('light.lampara_izquierda', temp).subscribe(() => {
          console.log(`Lámpara izquierda encendida con temperatura ${ambiente} (${temp}K)`);
        });
        return;
      }
    }
  
    // === Luces individuales ON/OFF ===
    // if (command.includes('encender luz izquierda') || command.includes('encender lámpara izquierda')) {
    //   this.turnOnLeftLamp();
    // } 
    if (command.includes('apagar luz izquierda') || command.includes('apagar lámpara izquierda')) {
      this.turnOffLeftLamp();
    } 
    // else if (command.includes('encender luz derecha')) {
    //   this.turnOnRightLamp();
    // } 
    else if (command.includes('apagar luz derecha')) {
      this.turnOffRightLamp();
    } 
    // else if (command.includes('encender lectura')) {
    //   this.turnOnReadingLamp();
    // } 
    else if (command.includes('apagar lectura')) {
      this.turnOffReadingLamp();
  
    // === Todas las luces ===
    } else if (command.includes('encender luces')) {
      this.turnOnLeftLamp();
      this.turnOnRightLamp();
      this.turnOnReadingLamp();
    } else if (command.includes('apagar luces')) {
      this.turnOffAllLamps();
  
    // === Modos ===
    } else if (command.includes('modo fiesta')) {
      this.startPartyMode();
    } else if (command.includes('desactivar fiesta')) {
      this.stopPartyMode();
    } else if (command.includes('modo alerta')) {
      this.startAlertMode();
    } else if (command.includes('desactivar alerta')) {
      this.stopAlertMode();
    } else if (command.includes('modo calido') || command.includes('modo cálido')) {
      this.startWarmMode();
    } else if (command.includes('desactivar calido') || command.includes('desactivar cálido')) {
      this.stopWarmMode();
  
    // === Color por voz en luz derecha (RGB) ===
    } else if (command.includes('encender luz derecha')) {
      const colorMap: { [key: string]: number[] } = {
        'rojo': [255, 0, 0],
        'verde': [0, 255, 0],
        'azul': [0, 0, 255],
        'amarillo': [255, 255, 0],
        'naranja': [255, 165, 0],
        'blanco': [255, 255, 255],
        'morado': [128, 0, 128],
        'rosa': [255, 105, 180]
      };
  
      const color = Object.keys(colorMap).find(c => command.includes(c));
      if (color) {
        this.apiService.setLampColor('light.lampara_derecha', colorMap[color]).subscribe(() => {
          console.log(`Luz derecha encendida en color ${color}`);
        });
      } else {
        console.log('Color no reconocido para la luz derecha.');
      }
  
    } else {
      console.log('Comando no reconocido:', command);
    }
  }
  
  
  
  toggleVoiceRecognition(): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  
    if (!SpeechRecognition) {
      console.error('API de reconocimiento de voz no soportada.');
      return;
    }
  
    if (!this.recognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'es-ES';
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 1;
  
      this.recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript.toLowerCase().trim();
        console.log('Comando detectado:', transcript);
        this.handleVoiceCommand(transcript);
      };
  
      this.recognition.onerror = (event: any) => {
        console.error('Error en el reconocimiento de voz:', event.error);
        this.isListening = false;
      };
  
      this.recognition.onend = () => {
        console.log('Reconocimiento de voz detenido.');
        if (this.isListening) {
          console.log('Reiniciando reconocimiento...');
          this.recognition.start(); // 🔁 sigue escuchando si está activo
        }
      };
    }
  
    if (!this.isListening) {
      this.recognition.start();
      this.isListening = true;
      console.log('Escuchando...');
    } else {
      this.recognition.stop();
      this.isListening = false;
      console.log('Micrófono desactivado.');
    }
  }  
  
}
