import { useEffect, useState } from 'react';
import { messagesApi } from '../../services/api';

interface Message {
  id: string;
  sender_id: string;
  recipient_id: string;
  subject?: string;
  body: string;
  message_type: string;
  priority: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  sender_first_name?: string;
  sender_last_name?: string;
  sender_email?: string;
  recipient_first_name?: string;
  recipient_last_name?: string;
  recipient_email?: string;
  property_name?: string;
}

export function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [view, setView] = useState<'inbox' | 'sent' | 'unread'>('inbox');
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showCompose, setShowCompose] = useState(false);
  const [composeData, setComposeData] = useState({
    recipient_id: '',
    subject: '',
    body: '',
    priority: 'normal',
  });

  useEffect(() => {
    loadMessages();
  }, [view]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const data = await messagesApi.list(view);
      setMessages(data.messages || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMessageClick = async (message: Message) => {
    setSelectedMessage(message);

    // Mark as read if unread and in inbox
    if (!message.is_read && view === 'inbox') {
      try {
        await messagesApi.markAsRead(message.id);
        loadMessages(); // Refresh to update unread count
      } catch (error) {
        console.error('Failed to mark message as read:', error);
      }
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await messagesApi.send(composeData);
      setShowCompose(false);
      setComposeData({
        recipient_id: '',
        subject: '',
        body: '',
        priority: 'normal',
      });
      if (view === 'sent') {
        loadMessages(); // Refresh sent messages
      }
      alert('Message sent successfully!');
    } catch (error: any) {
      alert(error.message || 'Failed to send message');
    }
  };

  const getPriorityBadge = (priority: string) => {
    const badges = {
      low: 'badge',
      normal: 'badge-pending',
      high: 'badge-in-progress',
      urgent: 'badge-failed',
    };
    return badges[priority as keyof typeof badges] || 'badge';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
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
        <h1 className="text-3xl font-bold text-gray-900">Messages</h1>
        <button
          onClick={() => setShowCompose(!showCompose)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showCompose ? 'Cancel' : '+ Compose'}
        </button>
      </div>

      {/* Compose Form */}
      {showCompose && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">New Message</h2>
          <form onSubmit={handleSendMessage} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Recipient User ID *
              </label>
              <input
                type="text"
                value={composeData.recipient_id}
                onChange={(e) => setComposeData({ ...composeData, recipient_id: e.target.value })}
                className="input"
                placeholder="Enter recipient user ID"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={composeData.subject}
                onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                className="input"
                placeholder="Message subject"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message *
              </label>
              <textarea
                value={composeData.body}
                onChange={(e) => setComposeData({ ...composeData, body: e.target.value })}
                className="input"
                rows={5}
                placeholder="Type your message..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={composeData.priority}
                onChange={(e) => setComposeData({ ...composeData, priority: e.target.value })}
                className="input"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => setShowCompose(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Send Message
              </button>
            </div>
          </form>
        </div>
      )}

      {/* View Tabs */}
      <div className="mb-6 flex gap-2">
        {[
          { key: 'inbox', label: 'Inbox', badge: unreadCount },
          { key: 'sent', label: 'Sent', badge: null },
          { key: 'unread', label: 'Unread', badge: null },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setView(tab.key as any)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors relative ${
              view === tab.key
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {tab.label}
            {tab.badge !== null && tab.badge > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Message List */}
        <div className="lg:col-span-1">
          <div className="card p-0 max-h-[600px] overflow-y-auto">
            {messages.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <div className="text-4xl mb-2">📭</div>
                <p>No messages</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  onClick={() => handleMessageClick(message)}
                  className={`p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedMessage?.id === message.id ? 'bg-blue-50' : ''
                  } ${!message.is_read && view === 'inbox' ? 'bg-blue-50/50' : ''}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className="font-semibold text-gray-900 truncate">
                      {view === 'sent'
                        ? `${message.recipient_first_name} ${message.recipient_last_name}`
                        : `${message.sender_first_name} ${message.sender_last_name}`}
                    </div>
                    <span className="text-xs text-gray-500">{formatDate(message.created_at)}</span>
                  </div>
                  {message.subject && (
                    <div className="text-sm font-medium text-gray-700 truncate mb-1">
                      {message.subject}
                    </div>
                  )}
                  <div className="text-sm text-gray-600 truncate">{message.body}</div>
                  {!message.is_read && view === 'inbox' && (
                    <div className="mt-2">
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                        New
                      </span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Message Detail */}
        <div className="lg:col-span-2">
          {selectedMessage ? (
            <div className="card">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    {selectedMessage.subject || 'No Subject'}
                  </h2>
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">
                      {view === 'sent' ? 'To' : 'From'}:{' '}
                    </span>
                    {view === 'sent'
                      ? `${selectedMessage.recipient_first_name} ${selectedMessage.recipient_last_name}`
                      : `${selectedMessage.sender_first_name} ${selectedMessage.sender_last_name}`}
                    {view === 'sent' && selectedMessage.recipient_email && (
                      <span className="text-gray-500"> ({selectedMessage.recipient_email})</span>
                    )}
                    {view !== 'sent' && selectedMessage.sender_email && (
                      <span className="text-gray-500"> ({selectedMessage.sender_email})</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(selectedMessage.created_at).toLocaleString()}
                  </div>
                </div>
                <span className={`badge ${getPriorityBadge(selectedMessage.priority)}`}>
                  {selectedMessage.priority}
                </span>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <div className="whitespace-pre-wrap text-gray-700">{selectedMessage.body}</div>
              </div>

              {selectedMessage.property_name && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Property:</span> {selectedMessage.property_name}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <div className="text-5xl mb-4">📨</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a message</h3>
              <p className="text-gray-600">Choose a message from the list to view its contents</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
