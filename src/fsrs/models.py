from datetime import datetime, timedelta
import copy
from typing import Tuple


def date_to_ms(t: datetime) -> int:
    return int(t.utcnow().timestamp() * 1000)


def ms_to_date(t: int) -> datetime:
    return datetime.fromtimestamp(t / 1000.0)


NEW = 0
LEARNING = 1
REVIEW = 2
RELEARNING = 3

AGAIN = 0
HARD = 1
GOOD = 2
EASY = 3


class ReviewLog:
    rating: int
    elapsed_days: int
    scheduled_days: int
    state: int

    def __init__(self, rating: int, elapsed_days: int, scheduled_days: int, state: int):
        self.rating = rating
        self.elapsed_days = elapsed_days
        self.scheduled_days = scheduled_days
        self.state = state


class Card:
    due: int
    stability: float
    difficulty: float
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: int
    last_review: int

    def __init__(self) -> None:
        self.due = 0
        self.stability = 0
        self.difficulty = 0
        self.elapsed_days = 0
        self.scheduled_days = 0
        self.reps = 0
        self.lapses = 0
        self.state = NEW
        self.last_review = 0


class SchedulingInfo:
    card: Card
    review_log: ReviewLog

    def __init__(self, card: Card, review_log: ReviewLog) -> None:
        self.card = card
        self.review_log = review_log


class SchedulingCards:
    again: Card
    hard: Card
    good: Card
    easy: Card

    def __init__(self, card: Card) -> None:
        self.again = copy.deepcopy(card)
        self.hard = copy.deepcopy(card)
        self.good = copy.deepcopy(card)
        self.easy = copy.deepcopy(card)

    def update_state(self, state: int):
        if state == NEW:
            self.again.state = LEARNING
            self.hard.state = LEARNING
            self.good.state = LEARNING
            self.easy.state = REVIEW
            self.again.lapses += 1
        elif state == LEARNING or state == RELEARNING:
            self.again.state = state
            self.hard.state = REVIEW
            self.good.state = REVIEW
            self.easy.state = REVIEW
        elif state == REVIEW:
            self.again.state = RELEARNING
            self.hard.state = REVIEW
            self.good.state = REVIEW
            self.easy.state = REVIEW
            self.again.lapses += 1

    def schedule(self, now: int, hard_interval: float, good_interval: float, easy_interval: float):
        self.again.scheduled_days = 0
        self.hard.scheduled_days = hard_interval
        self.good.scheduled_days = good_interval
        self.easy.scheduled_days = easy_interval
        self.again.due = now + int(timedelta(minutes=5).total_seconds() * 1000)
        self.hard.due = now + int(timedelta(days=hard_interval).total_seconds() * 1000)
        self.good.due = now + int(timedelta(days=good_interval).total_seconds() * 1000)
        self.easy.due = now + int(timedelta(days=easy_interval).total_seconds() * 1000)

    def record_log(self, card: Card, now: int) -> dict[int, SchedulingInfo]:
        return {
            AGAIN: SchedulingInfo(self.again, ReviewLog(AGAIN, self.again.scheduled_days, card.elapsed_days, card.state)),
            HARD: SchedulingInfo(self.hard, ReviewLog(HARD, self.hard.scheduled_days, card.elapsed_days, card.state)),
            GOOD: SchedulingInfo(self.good, ReviewLog(GOOD, self.good.scheduled_days, card.elapsed_days, card.state)),
            EASY: SchedulingInfo(self.easy, ReviewLog(EASY, self.easy.scheduled_days, card.elapsed_days, card.state)),
        }


class Parameters:
    request_retention: float
    maximum_interval: int
    easy_bonus: float
    hard_factor: float
    w: Tuple[float, ...]

    def __init__(self) -> None:
        self.request_retention = 0.9
        self.maximum_interval = 36500
        self.easy_bonus = 1.3
        self.hard_factor = 1.2
        self.w = (1., 1., 5., -0.5, -0.5, 0.2, 1.4, -0.12, 0.8, 2., -0.2, 0.2, 1.)
