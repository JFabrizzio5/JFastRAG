  Panel de Control - JFastRAG        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; } .task-item:hover { background-color: #f1f5f9; } .task-item input:checked + label { text-decoration: line-through; color: #64748b; } .chart-container { position: relative; width: 100%; max-width: 300px; height: 300px; margin: auto; }

JFastRAG 🚀
===========

Un panel de control interactivo para visualizar el progreso del proyecto RAG (Retrieval-Augmented Generation) construido con el framework [JFastFramework](https://github.com/JFabrizzio5/JFastFramework).

Progreso General
----------------

Este gráfico muestra el estado de finalización de todas las tareas del proyecto. Marca las casillas en las tarjetas de tareas para ver cómo se actualiza el progreso en tiempo real.

### 🐳 Dockerización

Encapsular la aplicación y el modelo en contenedores para un despliegue consistente y escalable.

*    Dockerizar el modelo de Machine Learning.
*    Dockerizar la API que sirve el modelo.

### 🔐 Seguridad

Implementar mecanismos de autenticación para proteger los recursos de la API.

*    Crear autenticación con JWT (JSON Web Tokens).

### 📊 Monitoreo

Desarrollar sistemas para controlar el uso y garantizar la estabilidad y el buen rendimiento del servicio.

*    Monitorear y establecer límites de uso por usuario.

let progressChart; const tasks = \[ { id: 'task1', completed: false }, { id: 'task2', completed: false }, { id: 'task3', completed: false }, { id: 'task4', completed: false }, \]; function calculateProgress() { const completedTasks = tasks.filter(task => task.completed).length; const pendingTasks = tasks.length - completedTasks; return \[completedTasks, pendingTasks\]; } function updateProgress(checkbox) { const task = tasks.find(t => t.id === checkbox.id); if (task) { task.completed = checkbox.checked; } const \[completed, pending\] = calculateProgress(); progressChart.data.datasets\[0\].data = \[completed, pending\]; const percentage = tasks.length > 0 ? Math.round((completed / tasks.length) \* 100) : 0; progressChart.options.plugins.tooltip.callbacks.title = () => \`${percentage}% Completado\`; progressChart.update(); } document.addEventListener('DOMContentLoaded', () => { const ctx = document.getElementById('progressChart').getContext('2d'); const \[initialCompleted, initialPending\] = calculateProgress(); progressChart = new Chart(ctx, { type: 'doughnut', data: { labels: \['Completado', 'Pendiente'\], datasets: \[{ data: \[initialCompleted, initialPending\], backgroundColor: \[ '#0d9488', // teal-600 '#e2e8f0' // slate-200 \], borderColor: '#ffffff', borderWidth: 4, hoverOffset: 8 }\] }, options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { padding: 20, font: { size: 14, family: 'Inter' } } }, tooltip: { enabled: true, backgroundColor: '#0f172a', titleFont: { size: 16, weight: 'bold', }, bodyFont: { size: 14, }, padding: 12, cornerRadius: 6, callbacks: { title: () => '0% Completado', label: function(context) { let label = context.label || ''; if (label) { label += ': '; } if (context.parsed !== null) { label += context.parsed + ' tarea(s)'; } return label; } } } } } }); });
