from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    company_name = State()
    activity_description = State()
    address_hours = State()
    work_hours = State()
    delivery_payment = State()

class AddFaqStates(StatesGroup):
    question = State()
    answer = State()

class AiGenerateFaqStates(StatesGroup):
    sphere = State()
    waiting_answer = State()
