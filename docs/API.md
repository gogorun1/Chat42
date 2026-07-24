# API 使用指南(团队内部文档)

这份文档讲的是接口该怎么用,不是完整的参数手册——参数细节参看自动生成的文档,服务跑起来之后直接看:

- Swagger UI: https://localhost/docs
- ReDoc: https://localhost/redoc
- 原始 OpenAPI schema: https://localhost/openapi.json

这几个页面会随接口改动自动更新。这份文档只补充 Swagger 覆盖不到的东西:鉴权具体是怎么打通的,以及新增接口时要注意哪些约定。

## Base URL(基础地址)

前端调用接口用的是**相对路径**(比如 `/auth/me`、`/health`),不是写死的绝对地址。开发环境里 `docker-compose.yml` 把 `VITE_API_URL` 设成了空字符串,所以 `fetch()` 会自动按当前页面的域名去发请求——而当前页面的域名永远是 `https://localhost`(经过 Nginx),因为宿主机上只对外开放了 Nginx 这一个端口。

前后端是刻意做成同源的,**不要再写死 `http://localhost:8000` 这类地址**——backend 的端口现在不对外映射了,这个地址根本连不上。

## 鉴权是怎么打通的

鉴权走的是 **cookie**,不是那种手动带 token 的方式:

- 登录、注册、OAuth 回调成功后,后端会种一个叫 `access_token` 的 cookie,带 `httpOnly`、`Secure`、`SameSite=Strict` 标志,里面存的是 JWT。前端 JS 读不到这个 cookie——这是故意设计的,防 XSS 攻击——所以你也不需要去读它。
- `frontend/src/lib/api.ts` 里封装的公共请求函数,每次请求都带上 `credentials: 'include'`,cookie 会自动跟着请求一起发出去。**永远不需要手动给请求加 token**,如果你发现自己在这么干,说明哪里想错了。
- 想知道"当前有没有登录"或者拿用户信息,用 `frontend/src/context/AuthContext.tsx` 里的 `useAuth()`:
  ```tsx
  const { user, loading, login, signup, logout } = useAuth()
  ```
  `user` 在 `/auth/me` 请求返回之前一直是 `null`;`loading` 表示这次初始检查还没结束,用它可以避免页面刚打开时闪一下"未登录"的样子。
- 想让某个页面必须登录才能进,用 `<ProtectedRoute />` 包一层(`frontend/src/components/ProtectedRoute.tsx`),可以照着 `App.tsx` 里 `/` 路由的写法抄。它会在确认没登录之后自动跳到 `/login`。
- 后端这边,任何需要拿到当前用户的接口,依赖 `app/core/deps.py` 里的 `get_current_user` 就行:
  ```python
  @router.get("/something")
  async def something(current_user: User = Depends(get_current_user)):
      ...
  ```
  cookie 缺失、无效或过期时,它会自动抛 `401`,不用自己再判断一遍。

### 目前已有的鉴权接口

| 接口 | 作用 |
|---|---|
| `POST /auth/signup` | 邮箱+密码注册,同时完成登录 |
| `POST /auth/login` | 邮箱+密码登录 |
| `POST /auth/logout` | 清除登录状态 |
| `GET /auth/me` | 拿当前用户信息,未登录返回 401 |
| `GET /auth/42/login` | 把浏览器带进 42 OAuth 授权流程 |
| `GET /auth/42/callback` | 42 授权完成后的跳转目标,不用自己调用 |

## 前端怎么调接口

用封装好的公共客户端,别自己现写 `fetch`:

```ts
import { api, ApiError } from '../lib/api'

const user = await api.get<User>('/auth/me')
await api.post('/some/endpoint', { foo: 'bar' })
```

只要状态码不是 2xx,就会抛出 `ApiError`(带 `.status` 和后端返回的 `detail` 错误信息)——接的时候捕获这个具体类型,别用泛泛的 catch 糊弄过去。

## 加新接口时,别漏了改 Nginx

`nginx.conf` 是显式白名单:只有匹配到的路径(`/health`、`/auth/`、`/docs`、`/redoc`、`/openapi.json`)才会转发给后端,其余一律默认转发给前端开发服务器。**如果你新增了一个后端路由前缀(比如 F8 的搜索/分析接口挂在 `/api/...` 下),记得同步去 `nginx/nginx.conf` 的后端 location 里补上这个前缀**,不然请求会被悄悄转发到前端,页面直接一片空白、连个报错都看不到,排查起来会很懵。

## 数据库怎么访问(后端)

接口函数用 `db: AsyncSession = Depends(get_db)`(来自 `app/core/database.py`)拿数据库会话,查询用 SQLAlchemy 2.0 的异步写法(`select(...)`、`await db.execute(...)`)。数据模型统一放在 `app/models/` 下;新增模型后要跑:

```sh
docker compose exec backend alembic revision --autogenerate -m "描述这次改动"
docker compose exec backend alembic upgrade head
docker compose exec -u root backend chown -R appuser:appuser /app  # 修复文件属主,见下面说明
```

最后这条 chown 有点烦人但必须跑:Alembic 生成的迁移文件是在容器内部创建的,如果发现宿主机上这些文件属主不对(正常情况下加了非 root 用户之后不该再遇到,但万一碰上了),跑这条命令就能修好。
