import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = '/api'; // Se usa el proxy
  private token = environment.apiToken;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    });
  }

  private post(endpoint: string, body: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/${endpoint}`, body, { headers: this.getHeaders() });
  }

  private get(endpoint: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/${endpoint}`, { headers: this.getHeaders() });
  }

  // ✅ Control de la lámpara izquierda
  turnOnLeftLamp(): Observable<any> {
    return this.post('services/light/turn_on', { entity_id: 'light.lampara_izquierda', brightness_pct: 10, kelvin: 1800 });
  }

  turnOffLeftLamp(): Observable<any> {
    return this.post('services/light/turn_off', { entity_id: 'light.lampara_izquierda' });
  }

  getLeftLampState(): Observable<any> {
    return this.get('states/light.lampara_izquierda');
  }

  // ✅ Control de la lámpara derecha
  turnOnRightLamp(): Observable<any> {
    return this.post('services/light/turn_on', { entity_id: 'light.lampara_derecha', brightness_pct: 100, rgb_color: [0, 0, 255] });
  }

  turnOffRightLamp(): Observable<any> {
    return this.post('services/light/turn_off', { entity_id: 'light.lampara_derecha' });
  }

  getRightLampState(): Observable<any> {
    return this.get('states/light.lampara_derecha');
  }

  // ✅ Control de la luz de lectura
  turnOnReadingLamp(): Observable<any> {
    return this.post('services/light/turn_on', { entity_id: 'light.lampara_de_lectura', brightness_pct: 10, kelvin: 1800 });
  }

  turnOffReadingLamp(): Observable<any> {
    return this.post('services/light/turn_off', { entity_id: 'light.lampara_de_lectura' });
  }

  getReadingLampState(): Observable<any> {
    return this.get('states/light.lampara_de_lectura');
  }
}
