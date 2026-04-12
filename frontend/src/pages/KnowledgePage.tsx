import { useState, useEffect } from 'react';
import { Card, Button, Input, Upload, List, Modal, Space, Tag, Typography, message } from 'antd';
import { PlusOutlined, UploadOutlined, DeleteOutlined, FileOutlined } from '@ant-design/icons';
import { knowledgeApi } from '../api';
import type { KnowledgeBase } from '../types';

const { Text } = Typography;

export default function KnowledgePage() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => { loadKBs(); }, []);

  const loadKBs = async () => {
    const data = await knowledgeApi.list();
    setKbs(data);
  };

  const createKB = async () => {
    if (!newName.trim()) return;
    await knowledgeApi.create(newName, newDesc);
    setCreateOpen(false);
    setNewName('');
    setNewDesc('');
    loadKBs();
    message.success('Knowledge base created');
  };

  const deleteKB = async (id: string) => {
    await knowledgeApi.delete(id);
    loadKBs();
    message.success('Deleted');
  };

  const handleUpload = async (kbId: string, file: File) => {
    setUploading(true);
    try {
      const res = await knowledgeApi.upload(kbId, file);
      if (res.error) {
        message.error(res.error);
      } else {
        message.success(`Uploaded: ${res.chunk_count} chunks`);
        loadKBs();
      }
    } catch {
      message.error('Upload failed');
    }
    setUploading(false);
  };

  const extColors: Record<string, string> = {
    '.pdf': 'red', '.txt': 'blue', '.md': 'green', '.docx': 'purple', '.doc': 'purple', '.xlsx': 'orange', '.xls': 'orange',
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Knowledge Bases</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          Create
        </Button>
      </div>

      <List
        grid={{ gutter: 16, column: 2 }}
        dataSource={kbs}
        renderItem={(kb) => (
          <List.Item>
            <Card
              title={kb.name}
              extra={
                <DeleteOutlined onClick={() => deleteKB(kb.id)} style={{ color: '#ff4d4f' }} />
              }
            >
              <Text type="secondary">{kb.description || 'No description'}</Text>
              <div style={{ margin: '12px 0' }}>
                <Text strong>{kb.document_count} documents</Text>
              </div>
              {kb.documents.map((doc) => (
                <div key={doc.id} style={{ marginBottom: 4 }}>
                  <FileOutlined style={{ marginRight: 4 }} />
                  <Text>{doc.filename}</Text>
                  <Tag color={extColors[doc.file_type] || 'default'} style={{ marginLeft: 8 }}>
                    {doc.file_type}
                  </Tag>
                  <Text type="secondary">{doc.chunk_count} chunks</Text>
                </div>
              ))}
              <Upload
                showUploadList={false}
                accept=".pdf,.txt,.md,.docx,.doc,.xlsx,.xls"
                beforeUpload={(file) => { handleUpload(kb.id, file as unknown as File); return false; }}
              >
                <Button icon={<UploadOutlined />} loading={uploading} style={{ marginTop: 8 }}>
                  Upload Document
                </Button>
              </Upload>
            </Card>
          </List.Item>
        )}
      />

      <Modal
        title="Create Knowledge Base"
        open={createOpen}
        onOk={createKB}
        onCancel={() => setCreateOpen(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="Name" value={newName} onChange={(e) => setNewName(e.target.value)} />
          <Input.TextArea placeholder="Description (optional)" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} rows={3} />
        </Space>
      </Modal>
    </div>
  );
}
