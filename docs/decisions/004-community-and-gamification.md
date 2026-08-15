# ADR 004: 社区与激励(F7)

- 状态:后端已实现(徽章、排行榜、竞猜端点全部完成并测试通过);前端待做
- 日期:2026-08-15

## 背景

`Chat42.pdf` 里 F7(社区与激励)原本的范围是四项:成就/徽章/排行榜、
"猜猫在哪"竞猜、好友、个人目击历史。但 [[003-user-profile]] 里已经决定把
"profile/avatar/friends/online"这四项**整体放进 F1 一次性做完**,不再拆给
F7——现在好友系统(搜索、加好友、接受、删除、在线状态)已经在
`backend/app/routers/users.py` 里实现并测试过了。

所以 F7 剩下的实际范围,收窄成打分表里对应的 **Gamification(Minor,1分)**:
成就/徽章、排行榜、"猜猫在哪"竞猜,外加一个后端已经就绪、只差前端的
**个人目击历史**页面。

## 现状(读代码确认过的)

- `Sighting` 模型(`backend/app/models/sighting.py`)字段是
  `id/user_id/zone_id/image_path/created_at`,没有积分/徽章相关字段。
- `Zone` 模型(`backend/app/models/zone.py`)只有 `id/slug/name`。
- `GET /sightings/`(`backend/app/routers/sightings.py`)**已经**按当前用户
  过滤、按 `created_at` 倒序返回——"个人目击历史"的后端不用另起端点,直接
  复用这个接口,只差前端页面。
- 部署栈(`docker-compose`:postgres/backend/frontend/nginx)里**没有定时任务
  /调度器**(没有 celery/cron 容器),这对"猜猫在哪"竞猜的每日结算是个硬约
  束:不能假设有后台任务在每天固定时间跑,只能在请求到达时现算(懒结算)。
- `User` 模型没有 `points`/`score` 字段。
- `app/services/notification_service.py` 已有通用的通知发送模式和
  `NotificationType` 枚举(`FRIEND_REQUEST` 已被 F1 用掉),如果要给"解锁新
  徽章"发通知,可以复用这套,但不是必须项。**枚举里已经预留了
  `BADGE_EARNED` 和 `GUESS_RESULT` 两个值**(在 F7 动手之前就有人加进去
  了)——后面接通知时直接用这两个,不要新建重复的类型。
- `nginx.conf` 按路由前缀逐条写 `location` 块(`/auth/`、`/sightings/`、
  `/users/`……),新加的路由前缀需要在这里补一条,否则外部请求 404。

## 决定

### 数据模型

徽章**定义**不建表——写死在后端代码的常量字典里(`code -> {name, description,
rule}`),这次比赛用不到后台可配置徽章的需求,建表反而是过度设计。只记录
"谁获得了哪个徽章":

```python
class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    badge_code: Mapped[str] = mapped_column(String(64), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "badge_code"),)
```

竞猜记录:

```python
class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # None = 还没结算
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "target_date"),)
```

规则:每人每天只能对"明天"提交一次竞猜——猜"明天目击数最多的 zone"。

**结算不用 cron,改成懒结算**:在读取竞猜历史或排行榜时,对所有
`target_date < 今天` 且 `is_correct IS NULL` 的记录现算——按 `target_date`
聚合当天每个 zone 的目击数,取数量最多的 zone 当"标准答案";如果那天完全没
有目击记录,这条记录标记不算分(不计入正确也不计入错误),避免"没人拍猫"
被反噬成大家都错。算完写回 `is_correct` 存库,下次不用重算。

积分**不落一个 `points` 字段**,查询时实时聚合:`目击数 + 竞猜正确数 × 10`,
排行榜按这个聚合结果排序。不落字段是为了避免"目击/竞猜结算/积分"三处状态
不同步的 bug。

### 端点(新建 `app/routers/gamification.py`)

| 端点 | 说明 |
|---|---|
| `GET /gamification/achievements` | 当前用户已获得的徽章列表 |
| `GET /gamification/leaderboard` | 排行榜(目击数 + 竞猜正确数×10 排序),分页 |
| `POST /gamification/predictions` | 提交"明天"竞猜(`zone_id`,每人每天一次) |
| `GET /gamification/predictions/me` | 我的竞猜历史(触发懒结算) |

个人目击历史直接用已有的 `GET /sightings/`,不新建端点。

### 徽章判定时机

在 `sightings.py` 的 `create_sighting` 成功创建目击记录之后,调用
`check_and_award_badges(db, user)`:查该用户的目击总数/去重 zone 数,和写死
的规则字典比对,新达成的规则写入 `user_badges`。`sightings.py` 这部分改动
也归你负责,不涉及跨人协调,直接改即可。

### 前端

- 新增一个成就/排行榜页面(或 Profile 页面新增一个 tab):展示已获得徽章 +
  排行榜列表。
- 首页/Dashboard 加一张"猜猫在哪"卡片:选 zone → 提交 → 显示"已提交,明天
  见分晓";如果今天已经提交过,显示已提交状态而不是表单。
- Profile 页面加"我的目击历史"区块,复用 `GET /sightings/`,按时间倒序展示
  缩略图 + zone + 时间。

## 不做的部分

- 不引入定时任务/cron 容器来结算竞猜——懒结算,请求到达时现算,足够满足
  单实例部署的需求。
- 不做徽章图标设计/自定义上传——用文字 + emoji 占位,不阻塞功能验收。
- 不做排行榜的 WebSocket 实时推送——排行榜刷新页面/轮询获取即可,不复用
  F5 的实时通道,避免不必要的耦合。
- 不做"连续登录天数"类徽章——目前没有登录流水表,徽章规则只基于目击行为,
  范围收窄避免过度设计。
- 不重做好友/头像/在线状态——已经在 F1(见 [[003-user-profile]])做完,这
  里不重复实现。

## 集成清单 / 需要和队友对接的点

- [x] `check_and_award_badges` 要挂在 `sightings.py` 的 `create_sighting`
      里——`sightings.py` 这部分改动也归你负责,不用再跨人协调,直接改。
- [ ] 竞猜结算依赖按"天"聚合 `Sighting`,需要和团队确认"一天"的边界口径——
      决定统一用 UTC 天,和后端其它时间戳(`created_at` 用
      `DateTime(timezone=True)`)保持一致,不用本地时区。
- [ ] `nginx.conf` 需要加一条 `/gamification/` 的转发规则。
- [ ] README 模块表/个人贡献部分要不要同步补上 F7 这块,按你的要求这次先
      不动 README。

## 分步实现顺序

1. ~~`UserBadge` + `Prediction` 表 + Alembic migration。~~ **已完成**
   (`backend/app/models/gamification.py`,migration
   `e5f6a7b8c9d0_add_badges_and_predictions.py`)。
2. ~~徽章规则常量 + `check_and_award_badges` service,挂进
   `sightings.py::create_sighting`。~~ **已完成**
   (`backend/app/services/gamification_service.py`,6 条单测全过,见
   `backend/tests/test_gamification_service.py`)。当前规则:首次目击、
   累计5/10/50次、集齐所有zone、连续7天打卡。
3. ~~`GET /gamification/achievements`、`GET /gamification/leaderboard`。~~
   **已完成**。排行榜排序用 `目击数 + 竞猜正确数×10`,没有落 `points` 字段。
4. ~~`POST /gamification/predictions` + 懒结算逻辑 +
   `GET /gamification/predictions/me`。~~ **已完成**
   (`backend/app/services/gamification_service.py::settle_pending_predictions`)。
5. ~~`nginx.conf` 加转发;后端测试(`test_gamification_router.py`)。~~
   **已完成**,7 条端点测试全过;另外手动 curl 走了一遍完整 HTTPS 链路
   (signup → 提交竞猜 → 重复提交 409 → 查询列表 → 查排行榜/成就)。
6. 前端:徽章/排行榜页 + 竞猜卡片 + Profile 页"我的目击历史"区块。**待做**。
7. 浏览器手动验证:攒够条件解锁徽章、排行榜排序正确、提交竞猜次日结算。
   **待做**(依赖第 6 步的前端页面)。
