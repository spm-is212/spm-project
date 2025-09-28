import React from 'react';

function TaskList({ tasks, onUpdateTask, onDeleteTask }) {
  return (
    <div className="task-list-container">
      <h2>My Tasks</h2>
      {tasks.length === 0 ? (
        <p>No tasks yet. Start by adding a new one!</p>
      ) : (
        <ul className="task-list">
          {tasks.map((task) => (
            <li key={task.id} className={`task-item ${task.status.toLowerCase().replace(' ', '-')}`}>
              <div className="task-details">
                <h3>{task.title}</h3>
                {task.description && <p>{task.description}</p>}
                <span className="task-status">Status: {task.status}</span>
              </div>
              <div className="task-actions">
                <button 
                  onClick={() => onUpdateTask(task.id, { status: task.status === 'To Do' ? 'In Progress' : 'To Do' })}
                  className="action-button update-button"
                >
                  Toggle Status
                </button>
                <button 
                  onClick={() => onDeleteTask(task.id)}
                  className="action-button delete-button"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default TaskList;


