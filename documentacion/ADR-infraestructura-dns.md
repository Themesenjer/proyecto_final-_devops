#  Registro de Decisiones de Arquitectura (ADR) - Resolución de Infraestructura Base y Reto DNS

**Proyecto:** Habit Tracker - Full Stack DevOps  
**Autor:** Pablo Javier Reyes  
**Fecha:** 13 de Julio del 2026  
**Estado:** Aprobado / Implementado en Producción  

---

## 1. Contexto del Proyecto y Objetivos de Infraestructura
Para soportar el ciclo de vida del proyecto "Habit Tracker", se requería el despliegue de una infraestructura base sólida en un servidor VPS (Ubuntu 24.04 LTS). Esta infraestructura debía garantizar la administración visual del entorno mediante Portainer, el enrutamiento de peticiones a través de un proxy inverso unificado y la provisión automatizada de seguridad de transporte criptográfico (HTTPS / TLS) para todos los subdominios de forma asíncrona mediante el reto DNS-01 con DuckDNS.

---

## 2. ADR 03: Downgrade Estratégico de Traefik (de v3 a v2.11) por Incompatibilidad de API

### Contexto:
Durante la implementación inicial de Traefik v3, el contenedor entró en un bucle infinito de reinicios y fallas de comunicación con el motor de Docker. Los logs reportaban reiteradamente:  
`"Docker API version is too old"` al intentar forzar de forma predeterminada la versión de la API `1.24`.

### Decisión de Arquitectura:
Se tomó la decisión técnica de realizar un downgrade controlado a **Traefik v2.11** en lugar de intentar parchear las directivas internas de compatibilidad de la v3.

### Justificación:
1. **Negociación Automática de API:** A diferencia de la v3 (que restringe agresivamente la comunicación con versiones anteriores de Docker Engine), Traefik v2.11 cuenta con un motor maduro y estable de auto-negociación de sockets.
2. **Estabilidad Probada:** La rama v2 de Traefik cuenta con una paridad de características del 100% para lo requerido en el proyecto (soporte nativo de DuckDNS, enrutamiento por etiquetas y TLS dinámico), garantizando cero fricciones de compatibilidad con el sistema operativo Ubuntu 24.04 moderno.

---

## 3. ADR 04: Implementación del Reto DNS-01 para DuckDNS y Fortalecimiento de Almacenamiento

### Contexto:
Para la validación del certificado SSL wildcard o por subdominios, el proveedor Let's Encrypt necesita certificar la posesión real del dominio. En lugar de usar retos HTTP (que exigen exponer rutas públicas), se seleccionó el reto DNS-01 modificando registros TXT temporalmente mediante la API de DuckDNS.

### Decisión de Arquitectura:
Se implementó el reto DNS-01 aislando el token del proveedor y encapsulando las llaves privadas de los certificados SSL en un archivo local ultra-restringido denominado `acme.json`.

### Justificación:
1. **Seguridad Absoluta en Capa de Red:** DNS-01 permite emitir certificados SSL sin abrir temporalmente puertos vulnerables ni requerir redirecciones públicas HTTP desde el inicio de la verificación.
2. **Manejo de Permisos Inmutables (POSIX):** El almacenamiento de certificados requiere de manera obligatoria que el archivo anfitrión (`acme.json`) posea únicamente permisos de lectura/escritura para el dueño del proceso (`chmod 600`), mitigando riesgos de extracción de credenciales TLS por otros usuarios del servidor.

---

## 4. Gestión de Errores Críticos y Lecciones Aprendidas en Producción

Durante la puesta en marcha de la infraestructura base, el equipo se enfrentó a bloqueos operativos que fueron depurados minuciosamente a través de la consola:

### Incidente 01: Error continuo de API obsoleta (Traefik v3.0)
* **Síntoma:** El proxy se mantenía "sordo" y no leía los contenedores expuestos por Docker, bloqueando el acceso a Portainer.
* **Causa:** Traefik v3 bloqueaba la comunicación al detectar el Docker Socket nativo del sistema moderno, asumiendo incompatibilidad.
* **Resolución:** Sustitución de la imagen en el archivo `docker-compose.yml` de `traefik:latest` a `traefik:v2.11`. El proxy levantó exitosamente reconociendo de inmediato el entorno en la primera carga.

### Incidente 02: Rechazo de Autenticación por DuckDNS (`Result (KO)`)
* **Síntoma:** Traefik fallaba al intentar actualizar los registros TXT para Let's Encrypt, obteniendo una respuesta directa `KO` de DuckDNS.
* **Causa:** Dos errores de tipografía críticos:
  1. Un carácter extra colado al final del token en el archivo de variables (el token real finalizaba en `b57` pero se guardó como `b579`).
  2. Traefik intentaba enviar el dominio completo (`devops-yavirac-pablo.duckdns.org`) en el parámetro `domains` de la API de DuckDNS, cuando el proveedor exige únicamente el prefijo del subdominio (`devops-yavirac-pablo`).
* **Resolución:** 
  1. Se depuró el token directamente usando la herramienta `curl` en consola para verificar de forma aislada la respuesta del servidor de DuckDNS.
  2. Se corrigió la sintaxis en el `docker-compose.yml` asignando el token exacto y agregando servidores DNS de resolución rápida externa (`8.8.8.8` y `1.1.1.1`) bajo la bandera `--certificatesresolvers.myresolver.acme.dnschallenge.resolvers` para asegurar una propagación instantánea libre de latencias locales.

### Incidente 03: Bloqueo de Escritura de Certificados SSL
* **Síntoma:** Los certificados no se generaban de manera persistente y los logs acusaban falta de permisos.
* **Causa:** El archivo de destino `acme.json` fue creado de forma predeterminada con permisos de lectura generales (`644`), lo cual es rechazado por Traefik como medida de protección criptográfica obligatoria.
* **Resolución:** Se detuvo el Stack, se vació el archivo corrupto con `echo "{}" > acme.json`, y se aplicaron estrictamente permisos Unix seguros mediante el comando:
  ```bash
  chmod 600 acme.json
* **Al reiniciar los contenedores, el proxy inverso pudo escribir las llaves TLS de forma segura y autorizar el candado HTTPS de manera inmediata.

### Incidente 04: Expiración del Instalador de Portainer (Security Timeout)
* *** Síntoma:** Tras dejar el servidor inactivo unos minutos, la URL de Portainer mostraba el error: "Your Portainer instance timed out for security purposes."
* *** Causa:** Por políticas nativas de endurecimiento de seguridad (hardening), Portainer bloquea su instalador web si no se registra un administrador dentro de los primeros 8 minutos de vida del contenedor.
* *** Resolución:** Se ejecutó el reinicio del contenedor desde la terminal del VPS con docker restart portainer para reiniciar el temporizador, se obtuvo el token de seguridad único desde los logs internos con docker logs portainer 2>&1 | grep -i "token", y se procedió a la configuración segura del usuario root.

### 5. Conclusión de la Evaluación de Infraestructura
* *** La infraestructura base actual garantiza una tolerancia total a fallos en el VPS. Gracias a la resolución del enrutamiento de sockets en Traefik v2.11 y el aseguramiento estricto de las directivas de seguridad de Let's Encrypt, el servidor se autogestiona por completo de forma independiente, dejando la máquina lista para albergar cualquier microservicio de desarrollo con despliegue continuo libre de configuraciones manuales de red.