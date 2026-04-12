import { useState, useEffect, useRef } from 'react';
import { Input, Button, List, Select, Space, Typography } from 'antd';
import { SendOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { sessionsApi, chatStream, knowledgeApi } from '../api';
import type { Session, Message, KnowledgeBase } from '../types';

const { Text } = Typography;

export default function ChatPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
    loadKBs();
  }, []);

  useEffect(() => {
    if (currentSession) loadMessages(currentSession);
  }, [currentSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamText]);

  const loadSessions = async () => {
    const data = await sessionsApi.list();
    setSessions(data);
    if (data.length > 0 && !currentSession) setCurrentSession(data[0].id);
  };

  const loadMessages = async (sessionId: string) => {
    const data = await sessionsApi.getMessages(sessionId);
    setMessages(data);
  };

  const loadKBs = async () => {
    const data = await knowledgeApi.list();
    setKnowledgeBases(data);
  };

  const createSession = async () => {
    const data = await sessionsApi.create();
    setSessions((prev) => [data, ...prev]);
    setCurrentSession(data.id);
    setMessages([]);
  };

  const deleteSession = async (id: string) => {
    await sessionsApi.delete(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (currentSession === id) {
      setCurrentSession(null);
      setMessages([]);
    }
  };

  const bindKB = async (sessionId: string, kbId: string | null) => {
    await sessionsApi.update(sessionId, { knowledge_base_id: kbId });
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, knowledge_base_id: kbId } : s))
    );
  };

  const sendMessage = () => {
    if (!input.trim() || !currentSession || streaming) return;
    const userMsg: Message = { id: Date.now(), role: 'human', content: input, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setStreaming(true);
    setStreamText('');

    chatStream(
      currentSession,
      input,
      (chunk) => setStreamText((prev) => prev + chunk),
      () => {
        setStreaming(false);
        setStreamText('');
        loadMessages(currentSession!);
      }
    );
  };

  const currentKB = sessions.find((s) => s.id === currentSession)?.knowledge_base_id;

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* Sidebar */}
      <div style={{ width: 260, borderRight: '1px solid #f0f0f0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: 12 }}>
          <Button type="primary" icon={<PlusOutlined />} block onClick={createSession}>
            New Chat
          </Button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => setCurrentSession(s.id)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                background: s.id === currentSession ? '#e6f4ff' : 'transparent',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Text ellipsis style={{ flex: 1 }}>{s.title}</Text>
              <DeleteOutlined
                onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                style={{ color: '#999', fontSize: 12 }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* KB Selector */}
        {currentSession && (
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #f0f0f0' }}>
            <Space>
              <Text>Knowledge Base:</Text>
              <Select
                allowClear
                placeholder="None"
                value={currentKB || undefined}
                onChange={(val) => bindKB(currentSession, val || null)}
                style={{ width: 200 }}
                options={knowledgeBases.map((kb) => ({ label: kb.name, value: kb.id }))}
              />
            </Space>
          </div>
        )}

        {/* Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          <List
            dataSource={messages}
            renderItem={(msg) => (
              <div style={{ marginBottom: 12, textAlign: msg.role === 'human' ? 'right' : 'left' }}>
                <div
                  style={{
                    display: 'inline-block',
                    maxWidth: '70%',
                    padding: '8px 12px',
                    borderRadius: 8,
                    background: msg.role === 'human' ? '#1677ff' : '#f5f5f5',
                    color: msg.role === 'human' ? '#fff' : '#000',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            )}
          />
          {streaming && streamText && (
            <div style={{ marginBottom: 12, textAlign: 'left' }}>
              <div
                style={{
                  display: 'inline-block',
                  maxWidth: '70%',
                  padding: '8px 12px',
                  borderRadius: 8,
                  background: '#f5f5f5',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {streamText}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{ padding: 16, borderTop: '1px solid #f0f0f0' }}>
          <Space.Compact style={{ width: '100%' }}>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={sendMessage}
              placeholder="Type a message..."
              disabled={!currentSession || streaming}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={sendMessage}
              loading={streaming}
              disabled={!currentSession}
            />
          </Space.Compact>
        </div>
      </div>
    </div>
  );
}
