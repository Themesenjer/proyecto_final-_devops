// Configuración de la URL del Backend (API)
const API_URL = "http://localhost:8000"; 

let isLoginMode = true;
let userToken = null; // Guardará el JWT tras el login

// Elementos del DOM
const authCard = document.getElementById("auth-card");
const trackerCard = document.getElementById("tracker-card");
const authForm = document.getElementById("auth-form");
const authTitle = document.getElementById("auth-title");
const authBtn = document.getElementById("auth-btn");
const toggleAuth = document.getElementById("toggle-auth");
const authActionText = document.getElementById("auth-action-text");
const habitsList = document.getElementById("habits-list");
const habitForm = document.getElementById("habit-form");
const logoutBtn = document.getElementById("logout-btn");

// Intercambiar vistas entre Login y Registro
toggleAuth.addEventListener("click", () => {
    isLoginMode = !isLoginMode;
    authTitle.innerText = isLoginMode ? "Iniciar Sesión" : "Crear Cuenta";
    authBtn.innerText = isLoginMode ? "Ingresar" : "Registrarse";
    authActionText.innerText = isLoginMode ? "Regístrate aquí" : "Inicia sesión aquí";
});

// Manejo del Login / Registro
authForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    
    const endpoint = isLoginMode ? `${API_URL}/auth/login` : `${API_URL}/auth/register`;
    
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.detail || "Error en la operación");
        
        if (isLoginMode) {
            userToken = data.token; // Guardamos el token simulación
            authCard.classList.add("hidden");
            trackerCard.classList.remove("hidden");
            loadHabits(); // Cargar el CRUD
        } else {
            alert("Usuario registrado con éxito. Ahora inicia sesión.");
            isLoginMode = true;
            authForm.reset();
            authTitle.innerText = "Iniciar Sesión";
            authBtn.innerText = "Ingresar";
        }
    } catch (error) {
        alert(error.message);
    }
});

// Obtener Hábitos (READ)
async function loadHabits() {
    try {
        const response = await fetch(`${API_URL}/habits`, {
            headers: { "Authorization": `Bearer ${userToken}` }
        });
        const habits = await response.json();
        habitsList.innerHTML = "";
        
        habits.forEach(habit => {
            const li = document.createElement("li");
            li.className = `habit-item ${habit.completed ? 'completed' : ''}`;
            li.innerHTML = `
                <span>${habit.name}</span>
                <div class="habit-actions">
                    <button onclick="toggleHabit(${habit.id}, ${!habit.completed})" class="btn-success">✓</button>
                    <button onclick="deleteHabit(${habit.id})" class="btn-danger">X</button>
                </div>
            `;
            habitsList.appendChild(li);
        });
    } catch (error) {
        console.error("Error cargando hábitos", error);
    }
}

// Crear Hábito (CREATE)
habitForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nameInput = document.getElementById("habit-name");
    
    try {
        await fetch(`${API_URL}/habits`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${userToken}`
            },
            body: JSON.stringify({ name: nameInput.value })
        });
        nameInput.value = "";
        loadHabits();
    } catch (error) {
        console.error("Error creando hábito", error);
    }
});

// Actualizar Hábito (UPDATE)
window.toggleHabit = async (id, completed) => {
    try {
        await fetch(`${API_URL}/habits/${id}`, {
            method: "PATCH",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${userToken}`
            },
            body: JSON.stringify({ completed })
        });
        loadHabits();
    } catch (error) {
        console.error("Error actualizando hábito", error);
    }
};

// Eliminar Hábito (DELETE)
window.deleteHabit = async (id) => {
    if(!confirm("¿Seguro que deseas eliminar este hábito?")) return;
    try {
        await fetch(`${API_URL}/habits/${id}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${userToken}` }
        });
        loadHabits();
    } catch (error) {
        console.error("Error eliminando hábito", error);
    }
};

// Cerrar Sesión
logoutBtn.addEventListener("click", () => {
    userToken = null;
    authForm.reset();
    trackerCard.classList.add("hidden");
    authCard.classList.remove("hidden");
});