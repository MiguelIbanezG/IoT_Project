import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  lightState: any;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.turnOffLight();
  }

  turnOffLight(): void {
    console.log("Enviando petición para apagar la luz...");
  
    this.apiService.turnOffLight('light.lampara_izquierda').subscribe(response => {
      console.log('Lámpara izquierda apagada:', response);
      this.lightState = response;
    }, error => {
      console.error('Error apagando la lámpara:', error);
    });
  }
  
}
