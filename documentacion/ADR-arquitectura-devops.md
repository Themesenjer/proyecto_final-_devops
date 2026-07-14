# 📑 Registro de Decisiones de Arquitectura (ADR) & Lecciones Aprendidas

**Proyecto:** Habit Tracker - Full Stack DevOps  
**Autor:** Pablo Javier Reyes  
**Fecha:** 13 de Julio del 2026  
**Estado:** Aprobado / Implementado en Producción  

---

## 1. Contexto del Proyecto y Objetivos de Arquitectura
El objetivo principal de este proyecto fue diseñar, empaquetar y desplegar una arquitectura web multicapa (Frontend, Backend y Persistencia) en un servidor VPS. Se buscó establecer un ciclo de vida de desarrollo de software gobernado por principios DevOps (automatización, inmutabilidad y despliegue continuo), aislando las aplicaciones en contenedores Docker y centralizando el tráfico mediante un proxy inverso con enrutamiento de subdominios y cifrado SSL.

---

## 2. ADR 01: Selección de Proxy Inverso y Orquestación de Subdominios

### Contexto:
Múltiples servicios independientes (Frontend, Backend, Portainer, pgAdmin) debían convivir dentro de la misma máquina física (VPS) utilizando una única dirección IP pública en los puertos estándar de navegación `80` (HTTP) y `443` (HTTPS).

### Decisión de Arquitectura:
Se seleccionó **Traefik Proxy** como balanceador de carga, proxy inverso y gestor de enrutamiento dinámico.

### Justificación:
1. **Integración Nativa con Docker:** Traefik detecta automáticamente la creación de contenedores nuevos leyendo los `labels` definidos en el archivo `docker-compose.yml`, eliminando la necesidad de reiniciar manualmente el proxy inverso al agregar servicios.
2. **Automatización de Certificados SSL:** Traefik interactúa de manera autónoma con la entidad certificadora **Let's Encrypt** para gestionar, generar y renovar los certificados SSL de todos los subdominios de forma transparente.

### Configuración del Enrutamiento:
Se estructuró el mapeo de subdominios únicos apuntando a los puertos internos expuestos dentro de la red del contenedor:
* `devops-yavirac-pablo.duckdns.org` ➔ Frontend Container (`Nginx` / Puerto interno `80`)
* `api.devops-yavirac-pablo.duckdns.org` ➔ Backend Container (`FastAPI` / Puerto interno `8000`)
* `portainer.devops-yavirac-pablo.duckdns.org` ➔ Portainer Panel (`Portainer` / Puerto interno `9000`)
* `db.devops-yavirac-pablo.duckdns.org` ➔ pgAdmin Web Application (`pgAdmin 4` / Puerto interno `80`)

---

## 3. ADR 02: Aislamiento y Seguridad de la Capa de Persistencia (PostgreSQL)

### Contexto:
La base de datos debe ser accesible únicamente para los microservicios que procesan o administran la información de la aplicación. Exponer el puerto de una base de datos directamente a internet representa una vulnerabilidad crítica de seguridad.

### Decisión de Arquitectura:
Se encapsuló el contenedor de **PostgreSQL** dentro de una **red interna privada de Docker (Docker Network)**, retirando cualquier asignación de subdominio, IP pública o exposición de puertos al exterior.

### Justificación:
1. **Zero-Trust Network:** Al no exponer el puerto por defecto `5432` a internet, se bloquean escaneos de puertos, ataques de fuerza bruta y accesos externos no autorizados.
2. **DNS Interno de Docker:** El Backend (FastAPI) y pgAdmin se comunican de forma segura con PostgreSQL utilizando el DNS nativo de Docker mediante el hostname `"prod_postgres_db"`.

---

## 4. Gestión de Errores Críticos y Lecciones Aprendidas en Producción

Durante las fases de integración y pruebas operativas en el servidor de producción, el equipo identificó y resolvió con éxito las siguientes anomalías críticas de red, seguridad y caché:

### Incidente 01: Error de CORS (Cross-Origin Resource Sharing)
* **Síntoma:** Al intentar registrar un usuario o realizar login desde el Frontend hacia la API en producción, el navegador bloqueaba la petición HTTP arrojando un fallo de conectividad.
* **Causa:** El navegador bloqueaba las llamadas de un subdominio a otro (del frontend a la API) como medida de protección cruzada, dado que la API no especificaba cabeceras que autorizaran explícitamente el origen de la consulta.
* **Resolución (Solución en Backend):** Se implementó y configuró la directiva `CORSMiddleware` de FastAPI en el archivo `backend/app.py`, permitiendo peticiones externas desde cualquier origen (`allow_origins=["*"]`), habilitando credenciales, métodos HTTP (`GET`, `POST`, `PATCH`, `DELETE`) y cabeceras personalizadas.

### Incidente 02: Bloqueo por Contenido Mixto e Invalidación de Certificado (`ERR_CERT_AUTHORITY_INVALID`)
* **Síntoma:** El frontend enviaba llamadas a la API que fallaban de inmediato en la consola con el error `net::ERR_CONNECTION_REFUSED` o `net::ERR_CERT_AUTHORITY_INVALID`.
* **Causa:** El navegador cliente cargaba el Frontend en protocolo no seguro (`http://`), pero las llamadas del script apuntaban a la URL cifrada de la API (`https://api...`). Por políticas de seguridad modernas, los navegadores bloquean peticiones mixtas para evitar la filtración de credenciales. Además, el navegador no confiaba de entrada en el certificado provisional autogenerado por Traefik mientras Let's Encrypt completaba la validación DNS asíncrona.
* **Resolución (Solución en Infraestructura):** 
  1. Se forzó el acceso general de la aplicación bajo protocolo cifrado seguro `https://`.
  2. Se configuró una excepción de desarrollo en el navegador de pruebas accediendo de forma directa a `https://api.devops-yavirac-pablo.duckdns.org/`, seleccionando "Opciones Avanzadas" y haciendo clic en "Continuar a la dirección (no segura)". Esto permitió al navegador almacenar localmente la firma del certificado intermedio del proxy, autorizando el flujo de datos.

### Incidente 03: Desincronización de Archivos Estáticos en Producción (Caché de Docker y Navegador)
* **Síntoma:** A pesar de haber modificado el archivo `script.js` para reemplazar `localhost:8000` por el subdominio de producción de la API y realizar el despliegue con éxito, el navegador seguía enviando las peticiones a `localhost`.
* **Causa:** El navegador web del cliente almacena en caché local persistente los archivos JavaScript para optimizar el rendimiento. Por otro lado, Docker en el servidor VPS reutilizaba la capa inmutable anterior de la imagen del Frontend al no detectar un cambio directo de estructura en el entorno del contenedor.
* **Resolución (Solución en Ciclo de Vida de Contenedores y Navegador):**
  1. **En Servidor (Portainer):** Se accedió al contenedor `prod_frontend` en Portainer, se ejecutó la acción **Recreate** y se activó explícitamente el interruptor **"Pull latest image"** para forzar a Docker a descartar la versión vieja en caché local y descargar la nueva imagen construida por el pipeline de GitHub Actions.
  2. **En Cliente (Navegador):** Se abrieron las herramientas de desarrollador (`F12`), se activó la opción **"Disable cache"** en la pestaña de red y se recargó la aplicación mediante la combinación de teclas **`Ctrl + F5`** para obligar al navegador a descargar el nuevo `script.js` desde el servidor VPS.

---

## 5. Conclusión de la Evaluación de Arquitectura
La solución actual no solo cumple con los requerimientos académicos, sino que implementa una metodología estándar de la industria de software. El aislamiento de la base de datos dentro de una red privada, el uso de un balanceador dinámico como Traefik y la automatización mediante GitHub Actions garantizan una plataforma escalable, segura y altamente tolerante a fallos.