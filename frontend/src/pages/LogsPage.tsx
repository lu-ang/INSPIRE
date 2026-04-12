import { useState, useEffect } from 'react';
import { Table, Select, Space, Typography, Tag, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { logsApi } from '../api';
import type { LogEntry } from '../types';

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [module, setModule] = useState<string | undefined>();
  const [level, setLevel] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadLogs(); }, [module, level]);

  const loadLogs = async () => {
    setLoading(true);
    const data = await logsApi.list({ module, level, limit: 100 });
    setLogs(data);
    setLoading(false);
  };

  const levelColors: Record<string, string> = {
    INFO: 'blue', WARN: 'orange', ERROR: 'red',
  };

  const columns = [
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (v: string) => <Tag color={levelColors[v] || 'default'}>{v}</Tag>,
    },
    {
      title: 'Module',
      dataIndex: 'module',
      key: 'module',
      width: 100,
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 160,
    },
    {
      title: 'Detail',
      dataIndex: 'detail',
      key: 'detail',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Operation Logs</Typography.Title>
        <Space>
          <Select
            allowClear
            placeholder="Module"
            value={module}
            onChange={setModule}
            style={{ width: 120 }}
            options={[
              { label: 'Chat', value: 'chat' },
              { label: 'Knowledge', value: 'knowledge' },
              { label: 'System', value: 'system' },
            ]}
          />
          <Select
            allowClear
            placeholder="Level"
            value={level}
            onChange={setLevel}
            style={{ width: 100 }}
            options={[
              { label: 'INFO', value: 'INFO' },
              { label: 'WARN', value: 'WARN' },
              { label: 'ERROR', value: 'ERROR' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={loadLogs}>Refresh</Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={loading}
        size="small"
        pagination={{ pageSize: 20 }}
      />
    </div>
  );
}
