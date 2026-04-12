import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { MessageOutlined, DatabaseOutlined, FileTextOutlined } from '@ant-design/icons';
import ChatPage from './pages/ChatPage';
import KnowledgePage from './pages/KnowledgePage';
import LogsPage from './pages/LogsPage';

const { Sider, Content } = Layout;

function AppLayout() {
  const location = useLocation();

  const menuItems = [
    { key: '/', icon: <MessageOutlined />, label: <Link to="/">Chat</Link> },
    { key: '/knowledge', icon: <DatabaseOutlined />, label: <Link to="/knowledge">Knowledge</Link> },
    { key: '/logs', icon: <FileTextOutlined />, label: <Link to="/logs">Logs</Link> },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={64} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 16 }}>
          IN
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          inlineCollapsed
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Content style={{ height: '100vh', overflow: 'hidden' }}>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
