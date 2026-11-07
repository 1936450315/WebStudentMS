# 学生管理系统 · Web V2.0

一个用于教学演示的学生信息管理系统：**FastAPI + SQLModel + SQLite** 后端，配 **单文件原生前端**（无框架、无 CDN、可离线打开）。

---

## 功能

- 学号 + 密码登录，登录后显示姓名与角色
- 登录后进入**工作台**：欢迎区、公告面板、快捷操作、账号信息
- **公告面板**：分类筛选（系统 / 教学 / 活动 / 紧急）、置顶、未读标记、全部已读、点击查看详情
- 学生列表：服务端分页（每页 10 / 20 / 50），斑马纹表格 + 悬停高亮
- 新增 / 编辑 / 删除学生（需要管理员权限，请求头携带 `x-sid`）
- 非管理员登录自动进入**只读模式**（新增/编辑/删除按钮置灰）
- 删除二次确认、成功/失败 Toast 提示
- 浅色 SaaS 风格界面，响应式布局

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI、SQLModel、SQLite、Uvicorn |
| 前端 | 单个 `index.html`：原生 HTML / CSS / JavaScript，无外部依赖 |

## 目录结构

```
web-V2.0/
├─ web.py            # 后端入口（FastAPI 应用）
├─ classInfo.db      # SQLite 数据文件（首次启动自动创建）
├─ index.html        # 前端页面（登录 + 管理台）
└─ README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn sqlmodel
```

### 2. 启动后端

```bash
python web.py
```

默认监听 `http://127.0.0.1:8080`。首次启动会自动建表，并在没有管理员时创建初始账号：

| 学号 | 密码 | 角色 |
|---|---|---|
| 2025001 | 1234 | admin |

### 3. 打开前端

- 直接双击 `index.html`，或
- 用浏览器打开 `file:///C:/Users/shenk/Desktop/web-V2.0/index.html`

后端已配置 CORS（`allow_origins=["*"]`），所以 `file://` 页面也能直接请求接口。
如果后端换了端口，在登录页底部「后端地址」里修改即可（会记住）。

---

## 工作台与公告面板

登录成功后默认进入**工作台**，顶部 tab 可在「工作台 / 学生管理」之间切换：

- **欢迎区**：按时间段显示问候语、当前账号角色与学号、当天日期
- **公告面板**：分类标签（系统 / 教学 / 活动 / 紧急）、置顶公告高亮、未读圆点、未读数、「全部已读」、点击打开公告详情
- **快捷操作**：学生管理、添加学生（仅管理员）、刷新列表
- **账号信息**：当前学号、姓名、角色、后端地址

> **公告数据说明**：后端目前没有公告接口，公告内容来自前端 `ANNOUNCEMENTS` 数组（示例数据）；已读状态保存在 `localStorage` 的 `webv2_ann_read` 键中。
> 后续接入真实公告时，新增后端接口（如 `GET /announcements`），把 `ANNOUNCEMENTS` 替换为接口返回的数据即可，其余交互不用改。

---

## 接口说明

| 方法 | 路径 | 参数 | 权限 | 说明 |
|---|---|---|---|---|
| POST | `/login` | query：`sid`、`password` | 无 | 成功返回 `{"msg":"登陆成功"}`（**不含角色**） |
| GET | `/students` | query：`skip=0`、`limit=10` | 无 | 分页返回学生列表（`StudentOut`） |
| GET | `/students/{sid}` | path：`sid` | 无 | 按学号查单个学生，含 `role` |
| POST | `/students` | JSON body（`Student`） | 管理员，Header `x-sid` | 201；学号重复返回 409 |
| PATCH | `/students/{sid}` | JSON body（`StudentModify`） | 管理员，Header `x-sid` | 局部更新，未传字段保持不变 |
| DELETE | `/students/{sid}` | path：`sid` | 管理员，Header `x-sid` | 删除学生 |

### 鉴权方式

`require_admin` 依赖读取请求头 `x-sid`（当前登录管理员的学号），在数据库中查出该学生并校验 `role == "admin"`。因此前端在 **POST / PATCH / DELETE** 时会自动带上：

```
x-sid: 2025001
```

### 前端如何知道角色

`POST /login` 只返回成功消息，没有角色字段。前端登录成功后会再请求 `GET /students/{sid}` 获取本人信息（`name`、`role`），用于显示身份并决定是否进入只读模式。

### 分页实现

后端没有提供总数接口，前端用 `limit = 每页条数 + 1` 预取一条来判断「是否还有下一页」，因此分页器不需要额外请求。

---

## 数据结构

```python
class Student(SQLModel, table=True):     # 数据库表
    id: Optional[int] = Field(default=None, primary_key=True)
    sid: int = Field(unique=True, index=True)
    passwd: str
    name: str
    age: int
    sex: str
    role: str

class StudentOut(SQLModel):              # 查询响应（不含密码）
    id: int
    sid: int
    name: str
    age: int
    sex: str
    role: str

class StudentModify(SQLModel):           # PATCH 请求体（全部可选）
    name: Optional[str] = None
    passwd: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    role: Optional[str] = None
```

---

## 前端实现要点

- **单文件、零 CDN**：所有样式与脚本内联，断网也能打开
- **设计 token**：CSS 变量按 Primitive → Semantic → Component 三层组织
- **无障碍**：正文对比度 ≥ 4.5:1、可见焦点环、按钮触控高度 ≥ 44px、原生 `<dialog>` 焦点管理、`prefers-reduced-motion` 降级
- **状态持久化**：登录态（学号 / 姓名 / 角色）与后端地址保存在 `localStorage`
- **错误提示**：解析 FastAPI 的 `detail`；422 校验错误会把数组拼成「字段名：原因」
- **分页边界**：删除当前页最后一条时自动回退上一页

---

## 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 页面提示「无法连接 …」 | 后端没启动，或端口不是 8080；先运行 `python web.py` |
| 403 非管理员 | 当前登录账号的 `role` 不是 `admin` |
| 409 学号重复 | 新增时学号已存在 |
| 404 学号不存在 / 密码错误 | 登录失败或查询的学号不存在 |
| 想重置数据 | 停止后端，删除 `classInfo.db`，重新启动会自动重建和管理员账号 |
| 8080 端口被占用 | 修改 `web.py` 末尾的 `port`，并在登录页更新「后端地址」 |

---

## 安全说明（仅教学用途）

- 密码在数据库和登录请求中均为**明文**，仅用于学习演示，请勿用于生产环境
- 使用 Header `x-sid` 作为身份凭证是简化方案，真实系统应使用 Session / JWT 等机制
- SQLite 数据文件与前端页面都在本地，如需局域网共享请自行加防护

---

## 许可

仅用于学习交流。