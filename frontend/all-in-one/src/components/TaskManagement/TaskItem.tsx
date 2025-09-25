import React, { useState } from 'react';
import type { Task } from '../../types/Task';

interface TaskItemProps {
  task: Task;
  onUpdateTask: (updatedTask: Task) => void;
  onDeleteTask: (taskId: string) => void;
  onToggleTaskStatus: (taskId: string) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, onUpdateTask, onDeleteTask, onToggleTaskStatus }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(task.title);
  const [editedDescription, setEditedDescription] = useState(task.description);
  const [editedDueDate, setEditedDueDate] = useState(task.dueDate || '');
  const [editedNotes, setEditedNotes] = useState(task.notes || '');
  const [editedAssignedTo, setEditedAssignedTo] = useState(task.assignedTo || '');

  const handleSave = () => {
    onUpdateTask({
      ...task,
      title: editedTitle,
      description: editedDescription,
      dueDate: editedDueDate,
      notes: editedNotes,
      assignedTo: editedAssignedTo,
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedTitle(task.title);
    setEditedDescription(task.description);
    setEditedDueDate(task.dueDate || '');
    setEditedNotes(task.notes || '');
    setEditedAssignedTo(task.assignedTo || '');
    setIsEditing(false);
  };

  const taskClassName = `task-item ${task.completed ? 'completed' : ''} ${task.dueDate && new Date(task.dueDate) < new Date() && !task.completed ? 'overdue' : ''}`;

  return (
    <li className={taskClassName}>
      {isEditing ? (
        <div className="edit-mode">
          <input type="text" value={editedTitle} onChange={(e) => setEditedTitle(e.target.value)} />
          <textarea value={editedDescription} onChange={(e) => setEditedDescription(e.target.value)}></textarea>
          <input type="date" value={editedDueDate} onChange={(e) => setEditedDueDate(e.target.value)} />
          <textarea value={editedNotes} onChange={(e) => setEditedNotes(e.target.value)}></textarea>
          <input type="text" value={editedAssignedTo} onChange={(e) => setEditedAssignedTo(e.target.value)} />
          <button className="save-button" onClick={handleSave}>Save</button>
          <button className="cancel-button" onClick={handleCancel}>Cancel</button>
        </div>
      ) : (
        <div className="task-details">
          <h3>{task.title}</h3>
          <p><strong>Description:</strong> {task.description}</p>
          {task.dueDate && <p><strong>Due Date:</strong> {task.dueDate}</p>}
          {task.notes && <p><strong>Notes:</strong> {task.notes}</p>}
          {task.assignedTo && <p><strong>Assigned To:</strong> {task.assignedTo}</p>}
          <div className="task-actions">
            <button className="toggle-status-button" onClick={() => onToggleTaskStatus(task.id)}>
              {task.completed ? 'Mark as Incomplete' : 'Mark as Complete'}
            </button>
            <button className="edit-button" onClick={() => setIsEditing(true)}>Edit</button>
            <button className="delete-button" onClick={() => onDeleteTask(task.id)}>Delete</button>
          </div>
        </div>
      )}
    </li>
  );
};

export default TaskItem;
