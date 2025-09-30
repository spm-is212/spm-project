import React, { useState } from 'react';
import TaskForm from './TaskForm';
import TaskList from './TaskList';
import './style.css';

function App() {
  const [tasks, setTasks] = useState([]);
  const [nextId, setNextId] = useState(1);

  const handleAddTask = (newTask) => {
    setTasks([...tasks, { id: nextId, ...newTask }]);
    setNextId(nextId + 1);
  };

  const handleUpdateTask = (id, updatedFields) => {
    setTasks(tasks.map(task =>
      task.id === id ? { ...task, ...updatedFields } : task
    ));
  };

  const handleDeleteTask = (id) => {
    setTasks(tasks.filter(task => task.id !== id));
  };

  return (
    <div className="App">
      <h1>Smart Task Manager</h1>
      <div className="main-content">
        <TaskForm onAddTask={handleAddTask} />
        <TaskList
          tasks={tasks}
          onUpdateTask={handleUpdateTask}
          onDeleteTask={handleDeleteTask}
        />
      </div>
    </div>
  );
}

export default App;
