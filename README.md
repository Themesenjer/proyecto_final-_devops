#  Habit Tracker - Full Stack DevOps Project

¡Bienvenido al proyecto **Habit Tracker**! Esta es una aplicación web moderna diseñada bajo una arquitectura de microservicios, totalmente contenerizada y desplegada de forma automatizada en un entorno de producción real utilizando prácticas de ingeniería DevOps.

---

##  Enlaces de Producción

Puedes interactuar con el ecosistema completo a través de los siguientes dominios en vivo:

*   **Frontend (Aplicación Web):** [https://devops-yavirac-pablo.duckdns.org](https://devops-yavirac-pablo.duckdns.org)
*   **Backend (Documentación Swagger API):** [https://api.devops-yavirac-pablo.duckdns.org/docs](https://api.devops-yavirac-pablo.duckdns.org/docs)

---

##  Arquitectura y Tecnologías

El proyecto se divide en componentes independientes que interactúan de forma aislada:

*   **Frontend:** Interfaz de usuario interactiva construida con HTML5, CSS3 y Vanilla JavaScript, servida de manera eficiente a través de un servidor web **Nginx**.
*   **Backend REST API:** API robusta y de alto rendimiento desarrollada con **FastAPI** (Python), encargada de la lógica de negocio, manejo de sesiones y endpoints CRUD.
*   **Base de Datos:** Motor relacional **PostgreSQL (15-Alpine)** para la persistencia segura de usuarios y hábitos.
*   **Orquestación de Contenedores:** Todo el entorno corre aislado mediante **Docker** y **Docker Compose**.
*   **Proxy Inverso & SSL:** **Traefik** administra el enrutamiento de subdominios y gestiona la generación automática de certificados SSL seguros con **Let's Encrypt**.
*   **Monitoreo y Gestión:** **Portainer** para la administración visual de contenedores y **pgAdmin 4** para la gestión de la base de datos en producción.

---

##  Pipeline de CI/CD (Automatización)

Este proyecto implementa Integración y Despliegue Continuo (CI/CD) a través de **GitHub Actions**:

1.  **Integración Continua (CI):** Ante cada cambio en la rama `main`, GitHub Actions compila de forma aislada las imágenes de Docker para el frontend y el backend.
2.  **Registro de Imágenes:** Las imágenes compiladas se versionan y almacenan de forma segura en **GitHub Packages (GHCR)**.
3.  **Despliegue Continuo (CD):** El pipeline se conecta de forma segura mediante **SSH** al servidor VPS de **Contabo**, actualiza el archivo de orquestación, descarga las últimas imágenes y reinicia los servicios sin interrumpir la disponibilidad de la plataforma.

---

##  Ejecución en Entorno Local

Si deseas replicar este proyecto en tu entorno local para desarrollo:

1. Clona este repositorio.
2. Asegúrate de tener instalado Docker Desktop.
3. Ejecuta el siguiente comando en tu terminal:
   ```bash
   docker compose -f docker-compose.local.yml up --build