document.addEventListener("DOMContentLoaded", () => {
    const taskForm = document.getElementById("task-form");
    const taskList = document.getElementById("task-list");

    let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
    let nextId = tasks.length > 0 ? Math.max(...tasks.map(task => task.id)) + 1 : 1;

    function saveTasks() {
        localStorage.setItem("tasks", JSON.stringify(tasks));
    }

    function renderTasks() {
        taskList.innerHTML = "";
        tasks.forEach(task => {
            const taskItem = document.createElement("li");
            taskItem.className = `task-item ${task.status.toLowerCase().replace(" ", "-")}`;
            if (task.dueDate && new Date(task.dueDate) < new Date() && task.status !== "Completed") {
                taskItem.classList.add("overdue");
            }

            taskItem.innerHTML = `
                <div class="view-mode">
                    <div class="task-details">
                        <h3>${task.title}</h3>
                        ${task.description ? `<p><strong>Description:</strong> ${task.description}</p>` : ""}
                        ${task.dueDate ? `<p><strong>Due Date:</strong> ${task.dueDate}</p>` : ""}
                        ${task.notes ? `<p><strong>Notes:</strong> ${task.notes}</p>` : ""}
                        ${task.assignedTo ? `<p><strong>Assigned To:</strong> ${task.assignedTo}</p>` : ""}
                        <p class="task-status"><strong>Status:</strong> ${task.status}</p>
                    </div>
                    <div class="task-actions">
                        <button class="toggle-status-button" data-id="${task.id}">Toggle Status</button>
                        <button class="edit-button" data-id="${task.id}">Edit</button>
                        <button class="delete-button" data-id="${task.id}">Delete</button>
                    </div>
                </div>
            `;
            taskList.appendChild(taskItem);
        });
        addEventListenersToTaskButtons();
    }

    function addEventListenersToTaskButtons() {
        document.querySelectorAll(".toggle-status-button").forEach(button => {
            button.onclick = (e) => {
                const id = parseInt(e.target.dataset.id);
                const taskIndex = tasks.findIndex(t => t.id === id);
                if (taskIndex > -1) {
                    const currentStatus = tasks[taskIndex].status;
                    let newStatus;
                    if (currentStatus === "To Do") {
                        newStatus = "In Progress";
                    } else if (currentStatus === "In Progress") {
                        newStatus = "Completed";
                    } else {
                        newStatus = "To Do";
                    }
                    tasks[taskIndex].status = newStatus;
                    saveTasks();
                    renderTasks();
                }
            };
        });

        document.querySelectorAll(".edit-button").forEach(button => {
            button.onclick = (e) => {
                const id = parseInt(e.target.dataset.id);
                const task = tasks.find(t => t.id === id);
                if (task) {
                    // Replace view mode with edit mode form
                    const taskItem = e.target.closest(".task-item");
                    taskItem.innerHTML = `
                        <div class="edit-mode">
                            <input type="text" class="edit-title" value="${task.title}">
                            <textarea class="edit-description">${task.description || ""}</textarea>
                            <input type="date" class="edit-dueDate" value="${task.dueDate || ""}">
                            <textarea class="edit-notes">${task.notes || ""}</textarea>
                            <input type="text" class="edit-assignedTo" value="${task.assignedTo || ""}">
                            <select class="edit-status">
                                <option value="To Do" ${task.status === "To Do" ? "selected" : ""}>To Do</option>
                                <option value="In Progress" ${task.status === "In Progress" ? "selected" : ""}>In Progress</option>
                                <option value="Completed" ${task.status === "Completed" ? "selected" : ""}>Completed</option>
                            </select>
                            <button class="save-edit-button" data-id="${task.id}">Save</button>
                            <button class="cancel-edit-button" data-id="${task.id}">Cancel</button>
                        </div>
                    `;
                    addEditModeEventListeners(task.id);
                }
            };
        });

        document.querySelectorAll(".delete-button").forEach(button => {
            button.onclick = (e) => {
                const id = parseInt(e.target.dataset.id);
                if (confirm("Are you sure you want to delete this task?")) {
                    tasks = tasks.filter(t => t.id !== id);
                    saveTasks();
                    renderTasks();
                }
            };
        });
    }

    function addEditModeEventListeners(id) {
        const taskItem = document.querySelector(`.task-item:has(button[data-id="${id}"].save-edit-button)`);
        if (!taskItem) return;

        taskItem.querySelector(".save-edit-button").onclick = () => {
            const taskIndex = tasks.findIndex(t => t.id === id);
            if (taskIndex > -1) {
                tasks[taskIndex].title = taskItem.querySelector(".edit-title").value;
                tasks[taskIndex].description = taskItem.querySelector(".edit-description").value;
                tasks[taskIndex].dueDate = taskItem.querySelector(".edit-dueDate").value;
                tasks[taskIndex].notes = taskItem.querySelector(".edit-notes").value;
                tasks[taskIndex].assignedTo = taskItem.querySelector(".edit-assignedTo").value;
                tasks[taskIndex].status = taskItem.querySelector(".edit-status").value;
                saveTasks();
                renderTasks();
            }
        };

        taskItem.querySelector(".cancel-edit-button").onclick = () => {
            renderTasks(); // Re-render to show view mode
        };
    }

    taskForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const title = document.getElementById("task-title").value;
        const description = document.getElementById("task-description").value;
        const dueDate = document.getElementById("task-dueDate").value;
        const notes = document.getElementById("task-notes").value;
        const assignedTo = document.getElementById("task-assignedTo").value;

        if (!title.trim()) {
            alert("Task title cannot be empty.");
            return;
        }

        const newTask = {
            id: nextId,
            title,
            description,
            dueDate,
            notes,
            assignedTo,
            status: "To Do", // Default status
        };
        tasks.push(newTask);
        nextId++;
        saveTasks();
        renderTasks();
        taskForm.reset();
    });

    renderTasks();
});
