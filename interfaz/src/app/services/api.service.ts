import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiBaseUrl;
  private token = environment.apiToken;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    });
  }

  post(endpoint: string, body: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/${endpoint}`, body, { 
      headers: this.getHeaders(),
      withCredentials: false // 🔹 Asegura que la política de CORS no esté bloqueando
    });
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
