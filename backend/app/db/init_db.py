import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine, Base, SessionLocal
from app.db.models import User, UserRole, MessageTemplate, Mailing, MessageDelivery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)

    # Check and create default admin
    admin = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL).first()
    if not admin:
        admin = User(
            email=settings.FIRST_SUPERUSER_EMAIL,
            full_name="System Administrator",
            role=UserRole.ADMIN.value,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_active=True,
            tags_attributes=["admin", "staff"],
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"Created default admin user: {settings.FIRST_SUPERUSER_EMAIL}")
    else:
        logger.info(f"Admin user already exists: {settings.FIRST_SUPERUSER_EMAIL}")

    # Seed sample templates if none exist
    if db.query(MessageTemplate).count() == 0:
        t1 = MessageTemplate(
            title="Приветственное письмо (Welcome Email)",
            subject="Добро пожаловать в нашу систему, {{ user.full_name }}!",
            body_content="""<h2>Здравствуйте, {{ user.full_name }}!</h2>
<p>Благодарим вас за подписку на наши информационные обновления.</p>
<p>Ваш email: <strong>{{ user.email }}</strong></p>
<hr />
<p style="font-size: 12px; color: #666;">
  Вы получили это письмо, так как подписаны на рассылку.
  <a href="{{ unsubscribe_url }}">Отписаться от рассылки</a>
</p>""",
            required_variables=["user.full_name", "user.email"],
        )
        t2 = MessageTemplate(
            title="Дайджест новостей и релизов",
            subject="Ежемесячный дайджест платформы: главное за месяц",
            body_content="""<h2>Привет, {{ user.full_name }}!</h2>
<p>Делимся ключевыми обновлениями нашей платформы за этот месяц:</p>
<ul>
  <li>Запущена асинхронная доставка уведомлений с аналитикой доставки в реальном времени</li>
  <li>Добавлена поддержка сегментации подписчиков по тегам</li>
  <li>Внедрен механизм автоматических повторных попыток (Retry Backoff)</li>
</ul>
<p>С наилучшими пожеланиями,<br />Команда Notification Service</p>
<hr />
<p style="font-size: 12px; color: #666;">
  <a href="{{ unsubscribe_url }}">Отписаться от рассылки</a>
</p>""",
            required_variables=["user.full_name"],
        )
        t3 = MessageTemplate(
            title="Важное системное уведомление",
            subject="[Важно] Плановое техническое обслуживание сервиса",
            body_content="""<h2>Уважаемый пользователь {{ user.full_name }}!</h2>
<p>Уведомляем вас о проведении плановых регламентных работ на серверах.</p>
<p>В период технических работ отправка сообщений будет временно поставлена на паузу с последующей автоматической досылкой.</p>
<hr />
<p style="font-size: 12px; color: #666;">
  <a href="{{ unsubscribe_url }}">Отписаться от рассылки</a>
</p>""",
            required_variables=["user.full_name"],
        )
        db.add_all([t1, t2, t3])
        db.commit()
        logger.info("Created 3 initial message templates")

    # Seed sample subscribers if none exist
    if db.query(User).filter(User.role == UserRole.SUBSCRIBER.value).count() == 0:
        subscribers = [
            User(
                email="alex.ivanov@example.com",
                full_name="Алексей Иванов",
                phone="+79001112233",
                role=UserRole.SUBSCRIBER.value,
                is_active=True,
                tags_attributes=["vip", "marketing"],
            ),
            User(
                email="olga.smirnova@example.com",
                full_name="Ольга Смирнова",
                phone="+79002223344",
                role=UserRole.SUBSCRIBER.value,
                is_active=True,
                tags_attributes=["marketing", "developers"],
            ),
            User(
                email="dmitry.kuznetsov@example.com",
                full_name="Дмитрий Кузнецов",
                phone="+79003334455",
                role=UserRole.SUBSCRIBER.value,
                is_active=True,
                tags_attributes=["developers"],
            ),
            User(
                email="elena.popova@example.com",
                full_name="Елена Попова",
                phone="+79004445566",
                role=UserRole.SUBSCRIBER.value,
                is_active=True,
                tags_attributes=["vip"],
            ),
            User(
                email="unsubscribed.user@example.com",
                full_name="Бывший Подписчик",
                phone="+79005556677",
                role=UserRole.SUBSCRIBER.value,
                is_active=False,
                tags_attributes=["churned"],
            ),
        ]
        db.add_all(subscribers)
        db.commit()
        logger.info("Created 5 initial sample subscribers")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
