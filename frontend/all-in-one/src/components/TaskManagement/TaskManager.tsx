import React, { useState, useEffect } from 'react';
// need to install uuid: npm install uuid
import { v4 as uuidv4 } from 'uuid';
import type { Task } from '../../types/Task';
import TaskForm from './TaskForm';
import TaskList from './TaskList';

const TaskManager: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>(() => {
    const savedTasks = localStorage.getItem('tasks');
    return savedTasks ? JSON.parse(savedTasks) : [];
  });

  useEffect(() => {
    localStorage.setItem('tasks', JSON.stringify(tasks));
  }, [tasks]);

  const addTask = (newTaskData: Omit<Task, 'id' | 'completed'>) => {
    const newTask: Task = {
      id: uuidv4(),
      ...newTaskData,
      completed: false,
    };
    setTasks((prevTasks) => [...prevTasks, newTask]);
  };

  const updateTask = (updatedTask: Task) => {
    setTasks((prevTasks) =>
      prevTasks.map((task) => (task.id === updatedTask.id ? updatedTask : task))
    );
  };

  const deleteTask = (taskId: string) => {
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
  };

  const toggleTaskStatus = (taskId: string) => {
    setTasks((prevTasks) =>
      prevTasks.map((task) =>
        task.id === taskId ? { ...task, completed: !task.completed } : task
      )
    );
  };

  return (
    <div className="container">
      <h1>Smart Task Manager</h1>
      <TaskForm onAddTask={addTask} />
      <TaskList
        tasks={tasks}
        onUpdateTask={updateTask}
        onDeleteTask={deleteTask}
        onToggleTaskStatus={toggleTaskStatus}
      />
    </div>
  );
};

export default TaskManager;
