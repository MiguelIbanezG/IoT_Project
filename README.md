# 🚀 IoT_Project  
**Innovación en Seguridad y Automatización**  

## 💡 Idea  
🌐 Crear una interfaz web para PC y móvil que pueda:  

	✅ Detectar el número de personas  
	✅ Identificar objetos peligrosos  
	✅ Reconocer actividades sospechosas  
	✅ Controlar luces con modos especiales (fiesta, alerta, etc.)  
	✅ Integrar sensores de movimiento, puertas abiertas, etc.  

## 🛠️ Instrucciones de Ejecución  

### 🔹 Local  
#### ⚙️ Backend  
```sh
cd modelo
gunicorn -w 1 -b 0.0.0.0:5000 --timeout 300 backend_server:app
```
#### 🎨 Frontend (Angular 9.1.13 y Node 16.20.2)
```sh
cd interfaz
nvm use 16
npx ng serve
```
