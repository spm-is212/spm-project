import React from 'react';
import type { Task } from '../types/Task';
import TaskItem from './TaskItem';

interface TaskListProps {
  tasks: Task[];
  onUpdateTask: (updatedTask: Task) => void;
  onDeleteTask: (taskId: string) => void;
  onToggleTaskStatus: (taskId: string) => void;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, onUpdateTask, onDeleteTask, onToggleTaskStatus }) => {
  return (
    <div className="task-list-section">
      <h2>My Tasks</h2>
      <ul id="task-list">
        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            onUpdateTask={onUpdateTask}
            onDeleteTask={onDeleteTask}
            onToggleTaskStatus={onToggleTaskStatus}
          />
        ))}
      </ul>
    </div>
  );
};

export default TaskList;
