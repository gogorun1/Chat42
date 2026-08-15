# ADR 004: 社区与激励(F7)

- 状态:已实现,前后端全部接通(`42map.tsx` 六个 tab——Report/History/Heat
  Map/Guess/Diary/Ranking——都在读写真实后端,不再有 mock 数据分支)
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

**实现记录(2026-08-15)**:新增独立页面 `frontend/src/pages/GamificationPage.tsx`
(路由 `/gamification`,`Layout.tsx` 导航栏加了入口),包含竞猜表单 + 徽章展示 +
排行榜,全部接的是本 ADR 的真实端点。`ProfilePage.tsx` 加了"My sighting
history"区块,复用 `GET /sightings/`。

**发现一个需要和 F4 对齐的点**:`frontend/src/components/42map.tsx`(F4 的地图
组件)里**已经有**一套"guess"(猜猫在哪)、"ranking"(排行榜)、"history"
(目击历史)、"heat"(热力图)的 UI——但数据全是本地 mock(`../data/cat`、
`../data/sighting`,zone id 是 `entrance`/`f0`/`f1` 这种,不对应后端
`zones` 表的 `slug`),竞猜逻辑也是纯前端算分,完全没接后端。这次 F7 的实现
**没有碰这个文件**,按你的要求先不找 F4 协调——但这意味着现在 app 里同时存在
两套"猜猫"体验:`/gamification` 是接了真实后端的,`42map.tsx` 里的是纯本地
假数据的。后面要么把 `42map.tsx` 的 mock 逻辑换成调用
`/gamification/predictions`、`/gamification/leaderboard`,要么两边保留但要
避免用户困惑(比如两处积分对不上)。这个需要你和 F4 那边对一下打算怎么处理。

**已解决的前置阻塞项(2026-08-15)**:`zones` 表原本的 5 个占位 zone
(a-block/b-block/c-block/cluster/outside,F2 migration 种的)已经换成
F4 地图里真实的 13 个 zone(migration
`f6a7b8c9d0e1_replace_zones_with_real_campus_map.py`),slug 直接用她
`42map.tsx` 里 `zones` 对象的 key(`entrance`/`cantine_m1`/`f0`/`f1`/…),
她本地的 zone 元数据(图片、楼层)可以按 slug 对上后端返回的 `id`。当时
DB 里没有任何 `sightings` 引用旧 zone,唯一一条测试用的 `predictions` 行随
外键 `ON DELETE CASCADE` 一起被清掉了,不是数据迁移,是直接换。现在
`GET /sightings/zones` 返回的就是这 13 个真实 zone(手动 curl 验证过)。

**规则分歧已决定(2026-08-15,你和 F4 对接后拍板)**:猜**今天**,保持 F4 原本
的前端逻辑不变(即时判定,不等隔天结算)。

这个决定的后果需要记一下:
- 已经把 `42map.tsx` 里 `Report`/`History`/`Heat Map` 用的 `lastSighting` 换
  成了一个真实计算出来的 `latestSighting`(取 `GET /search/sightings` 最新
  一条,按 `zone_id` 反查本地 slug),`Guess`/"Last Seen 卡片"/地图上的猫图
  标现在判定的是"最新一条真实目击",不再是写死的 `cantine_m1`/`test6`/
  `7:42`。数据库里还没有真实 sighting 时会 fallback 回原来的 mock,不会
  报错。
- `handleGuess` 的即时判分逻辑(花1分猜、猜中给3分)**保持不变**,只是换了
  判定依据的数据源。
- 我这边之前做的 `/gamification/predictions`(猜明天、懒结算)现在**没有
  被这次决定的 Guess UI 使用**——两边不是同一个游戏。是留着(可能以后有别
  的用途,比如做一个独立的"每日竞猜"功能),还是干脆砍掉,这个还没定,不
  在这次改动范围内,先不动它。

**"points 不落库"这个问题已解决(2026-08-15)**:新增 `users.guess_points`
字段(migration `a7b8c9d0e1f2_add_guess_points_to_users.py`,起始值 **5**,
不是 F4 原本 mock 的 120)+ `POST /gamification/guess` 端点——服务端拿
"最新一条真实目击"当标准答案判定对错、真实扣/加分并落库,不再是前端本地
算分。`GET /gamification/leaderboard` 的 `score` 现在是
`目击数 + 竞猜正确数×10 + guess_points`,首页"⭐ pts"/"🏆 Rank"也换成了
真实查排行榜取自己那一条,不再是硬编码的"120 pts"/"Rank #12"——两处现在
显示的是同一个数字。`handleGuess` 的判分文案/交互没变,只是从"本地
`setPoints`"换成了"调用后端、拿返回值刷新 `useAuth()` 的 `user`"。

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
6. ~~前端:徽章/排行榜页 + 竞猜卡片 + Profile 页"我的目击历史"区块。~~
   **已完成**(`GamificationPage.tsx` + `ProfilePage.tsx` 改动),TS 类型检
   查通过(排除已知无关的 `Plot.ts` 缺失问题)。
7. 浏览器手动验证:攒够条件解锁徽章、排行榜排序正确、提交竞猜次日结算。
   **待做**——这一步我(Claude)没有浏览器可以操作,需要你本人登录点一遍
   `/gamification` 和 profile 页面确认视觉/交互没问题。

## 收尾(2026-08-15):`42map.tsx` 六个 tab 全部接通真实数据

第 118 行那条"需要和 F4 对齐"的记录里提到的"两套猜猫体验并存"问题,现在
按你和 F4 拍板的方案(猜今天、保持她的前端逻辑)解决了——不是二选一砍掉一
套,是把 F4 的地图 UI 接到了真实后端上:

- **Report**:`POST /sightings/`(F2),真实猫检测。
- **History / Heat Map**:F8 的 `GET /search/sightings`(全校数据)。
- **Guess**:`POST /gamification/guess`,服务端拿"最新一条真实目击"当答案
  判定,`users.guess_points` 落库(起始 5 分)。
- **Diary**:F9 的 `GET /ai/diary`(顺手发现并修了 `nginx.conf` 缺失
  `/ai/` 转发的问题,这是 F9 遗留的、和 F7 无关的 gap)。
- **Ranking**:`GET /gamification/leaderboard`。

`data/cat.ts`/`data/sighting.ts` 这两个 mock 文件还在,只作为"数据库里还
没有真实数据时"的 fallback(比如刚部署、一条 sighting 都没有的时候),不
再是主数据源。首页"⭐ pts"/"🏆 Rank"和 Gamification 页排行榜、地图里的
Ranking tab,现在三处显示的是同一个数字。
