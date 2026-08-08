"""
Call `notify_user()` (or `broadcast_sighting()`) from other features instead of
writing to the notifications table directly, so persistence + the live push
never drift apart.

Example (from F2's create_sighting, in app/routers/sightings.py, right after
`await db.refresh(sighting)` / `sighting.zone = zone`):

    from app.services.notification_service import broadcast_sighting
    await broadcast_sighting(sighting, zone_name=zone.name)

Note on cats: F2 landed with NO separate Cat entity — a Sighting only links
to a Zone, not to an identified cat (the "zero-shot cat detection" just
confirms the photo contains *a* cat, not *which* cat). So the broadcast
message is zone-based ("A cat was just spotted in X!"), not cat-named. If a
future feature adds cat identity, this is the function to extend.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket_manager import manager
from app.models.notification import Notification, NotificationType
from app.models.sighting import Sighting
from app.schemas.notification import NotificationCreate


async def notify_user(db: AsyncSession, payload: NotificationCreate) -> Notification:
    notification = Notification(
        user_id=payload.user_id,
        type=payload.type,
        title=payload.title,
        body=payload.body,
        data=payload.data,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    await manager.send_to_user(
        payload.user_id,
        {
            "channel": "notification",
            "id": str(notification.id),
            "type": notification.type.value,
            "title": notification.title,
            "body": notification.body,
            "data": notification.data,
            "created_at": notification.created_at.isoformat(),
        },
    )
    return notification


async def broadcast_sighting(sighting: Sighting, zone_name: str) -> None:
    """
    Public, campus-wide "a cat was just spotted" push (F5 core requirement).
    This is a live-only broadcast — no per-user notification row, since it's
    not addressed to anyone in particular. Followers/watchers with a stronger
    per-user interest would go through `notify_user` with SIGHTING_NEARBY
    instead (not built yet — there's no "follow a zone" concept in F7 yet).

    Takes the already-persisted Sighting directly (rather than individual
    fields) since F2's router already has the full object in hand after
    commit — no db argument needed here, this function only pushes, it
    doesn't write anything.
    """
    image_url = f"/uploads/{sighting.image_path}"
    await manager.broadcast(
        {
            "channel": "sighting",
            "sighting_id": sighting.id,
            "zone_id": sighting.zone_id,
            "zone_name": zone_name,
            "created_at": sighting.created_at.isoformat(),
            "image_url": image_url,
            "message": f"A cat was just spotted in {zone_name}!",
        },
        exclude_user=sighting.user_id,
    )