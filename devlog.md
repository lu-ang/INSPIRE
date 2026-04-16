## 4.13
init langgragh demo
switch to cursor

### LangGraph Demo v1
- LangGraph + LangChain + qwen-max CLI demo
- `chat_agent.py` + `requirements.txt`

### INSPIRE Full Stack v0.1
- Backend: FastAPI + LangGraph Agent + ChromaDB + SQLite
- Frontend: React + TypeScript + Vite + Ant Design
- Features: RAG, KB management, long/short-term memory, logs
- Start backend: `cd backend && uvicorn main:app --reload`
- Start frontend: `cd frontend && npm run dev`

- 
## new request
1, 增加功能，账户登录注册功能，普通用户和管理员，能查看各自的知识库和自己个人对话纪录，管理员能看到所有的对话记录和所有的知识库，
2，增加功能，增加个人中心可以更换头像，用户名，密码信息等
3，增加功能，session可以自动总结session主题而不是默认的newchat，用户也可以自定义主题名字，
4，界面美化，增加自选主题， 皮肤色调，黑夜，别的颜色等
5，界面美化，chat页面可以显示用户和机器人的头像，以及各自的对话框，机器人回答信息返回前，增加一个转圈加载的“助手思考中”
