import logging
from typing import List
from django.db import transaction
from django.contrib.auth import get_user_model
from ..models.circulation import Badge, BadgeAward, Transfer

logger = logging.getLogger(__name__)
User = get_user_model()


class BadgeService:
    """
    Evaluates and awards gamification badges based on circulation milestones.
    Implements idempotent milestone evaluation and award logging.
    """

    DEFAULT_BADGES = [
        {
            "slug": "first_book_donated",
            "title_fa": "آغازگر مهربانی",
            "title_en": "First Kindness",
            "description_fa": "اولین اهدای کتاب در پلتفرم تفاخر",
            "description_en": "Donated your very first book on Tafakor",
            "icon": "HeartHandshakeIcon",
            "threshold": 1,
            "criteria": Badge.Criteria.TRANSFERS_GIVEN,
            "order": 1,
        },
        {
            "slug": "book_ambassador",
            "title_fa": "سفیر کتاب",
            "title_en": "Book Ambassador",
            "description_fa": "اهدای ۵ جلد کتاب و ترویج فرهنگ مطالعه",
            "description_en": "Donated 5 books and promoted reading culture",
            "icon": "BookOpenIcon",
            "threshold": 5,
            "criteria": Badge.Criteria.TRANSFERS_GIVEN,
            "order": 2,
        },
        {
            "slug": "city_librarian",
            "title_fa": "کتابدار شهر",
            "title_en": "City Librarian",
            "description_fa": "اهدای ۲۰ جلد کتاب در شبکه تفاخر",
            "description_en": "Donated 20 books across the Tafakor circulation network",
            "icon": "AwardIcon",
            "threshold": 20,
            "criteria": Badge.Criteria.TRANSFERS_GIVEN,
            "order": 3,
        },
        {
            "slug": "avid_reader",
            "title_fa": "کتاب‌خوان پرشور",
            "title_en": "Avid Reader",
            "description_fa": "دریافت و مطالعه ۳ جلد کتاب از شبکه گردش",
            "description_en": "Received and read 3 books from the circulation network",
            "icon": "SparklesIcon",
            "threshold": 3,
            "criteria": Badge.Criteria.TRANSFERS_RECEIVED,
            "order": 4,
        },
        {
            "slug": "shelf_benefactor",
            "title_fa": "یار قفسه‌های تفاخر",
            "title_en": "Shelf Benefactor",
            "description_fa": "سپردن ۳ جلد کتاب به قفسه‌ها و کیوسک‌های فیزیکی",
            "description_en": "Deposited 3 books into Tafakor public physical shelves",
            "icon": "LibraryIcon",
            "threshold": 3,
            "criteria": Badge.Criteria.STATION_DEPOSITS,
            "order": 5,
        },
    ]

    @classmethod
    def ensure_default_badges_exist(cls) -> None:
        """
        Idempotently seeds default system badges if they are not yet registered.
        """
        for item in cls.DEFAULT_BADGES:
            Badge.objects.get_or_create(
                slug=item["slug"],
                defaults=item
            )

    @classmethod
    @transaction.atomic
    def evaluate_user_badges(cls, user) -> List[Badge]:
        """
        Evaluates circulation criteria for a user and awards any newly earned badges.
        Returns the list of newly awarded badges.
        """
        if not user or not user.is_authenticated:
            return []

        # 1. Gather user metrics with zero N+1 overhead
        transfers_given_count = Transfer.objects.filter(
            from_user=user,
            status=Transfer.Status.CONFIRMED
        ).count()

        transfers_received_count = Transfer.objects.filter(
            to_user=user,
            status=Transfer.Status.CONFIRMED
        ).count()

        station_deposits_count = Transfer.objects.filter(
            from_user=user,
            method=Transfer.Method.STATION_DEPOSIT,
            status=Transfer.Status.CONFIRMED
        ).count()

        # 2. Evaluate unearned badges
        already_earned_ids = set(
            BadgeAward.objects.filter(user=user).values_list("badge_id", flat=True)
        )
        badges = Badge.objects.exclude(id__in=already_earned_ids)

        newly_earned: List[Badge] = []
        for badge in badges:
            qualifies = False
            if badge.criteria == Badge.Criteria.TRANSFERS_GIVEN:
                qualifies = transfers_given_count >= badge.threshold
            elif badge.criteria == Badge.Criteria.TRANSFERS_RECEIVED:
                qualifies = transfers_received_count >= badge.threshold
            elif badge.criteria == Badge.Criteria.STATION_DEPOSITS:
                qualifies = station_deposits_count >= badge.threshold

            if qualifies:
                BadgeAward.objects.create(user=user, badge=badge)
                newly_earned.append(badge)
                logger.info("Badge '%s' awarded to user %s", badge.slug, user.id)

        return newly_earned

