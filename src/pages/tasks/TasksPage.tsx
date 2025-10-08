import { useEffect, useState } from 'react';
import { tasksApi } from '../../services/api';
import type { Task } from '../../types';

export function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    try {
      const filters = filter === 'all' ? {} : { status: filter };
      const data = await tasksApi.list(filters);
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      PENDING: 'badge-pending',
      IN_PROGRESS: 'badge-in-progress',
      COMPLETED: 'badge-completed',
      CANCELLED: 'badge-failed',
    };
    return badges[status as keyof typeof badges] || 'badge';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Tasks</h1>
        <button className="btn-primary">+ Add Task</button>
      </div>

      <div className="mb-6 flex gap-2">
        {['all', 'PENDING', 'IN_PROGRESS', 'COMPLETED'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status === 'all' ? 'All' : status.replace('_', ' ')}
          </button>
        ))}
      </div>

      {tasks.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">✓</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks found</h3>
          <p className="text-gray-600 mb-6">
            {filter === 'all'
              ? 'Create your first task to get started'
              : `No ${filter.toLowerCase().replace('_', ' ')} tasks`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div key={task.id} className="card hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
                    <span className={`badge ${getStatusBadge(task.status)}`}>
                      {task.status}
                    </span>
                    {task.priority && task.priority !== 'MEDIUM' && (
                      <span className="text-xs text-gray-600">
                        Priority: {task.priority}
                      </span>
                    )}
                  </div>
                  {task.description && (
                    <p className="text-gray-600 mb-2">{task.description}</p>
                  )}
                  <div className="flex gap-4 text-sm text-gray-500">
                    {task.property_name && <span>🏠 {task.property_name}</span>}
                    {task.due_date && (
                      <span>
                        📅 Due: {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                    <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <button className="btn-secondary ml-4">View</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
