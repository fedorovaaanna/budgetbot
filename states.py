from aiogram.fsm.state import StatesGroup, State

class Onboarding(StatesGroup):
    expense_categories = State()
    income_categories = State()
