"""
Основной файл Flask приложения
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import json
import sqlite3
import hashlib
import os
from subscription_system import save_user_contact_info
from mlm_system import get_db, generate_referral_code, create_referral_structure

# Получаем абсолютные пути к директориям
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, 'static')
templates_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, 
            static_folder=static_dir,
            template_folder=templates_dir)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================
# ОБНАРУЖЕНИЕ СУИЦИДАЛЬНЫХ МЫСЛЕЙ
# ============================================

def detect_suicidal_thoughts(message):
    """
    Обнаруживает суицидальные мысли в сообщении пользователя
    
    Returns:
        bool: True если обнаружены суицидальные мысли
    """
    if not message:
        return False
    
    message_lower = message.lower().strip()
    
    # Ключевые фразы, указывающие на суицидальные мысли
    suicidal_phrases = [
        'я хочу умереть',
        'мне хочется умереть',
        'хочу умереть',
        'хочется умереть',
        'хочу покончить',
        'покончить с собой',
        'покончить жизнь',
        'свести счеты с жизнью',
        'покончить самоубийством',
        'совершить самоубийство',
        'суицид',
        'суицидальные мысли',
        'не хочу жить',
        'не хочется жить',
        'лучше умереть',
        'лучше бы умереть',
        'хочу уйти из жизни',
        'уйти из жизни',
        'свести счеты',
        'не вижу смысла жить',
        'не хочу больше жить',
        'хочу навсегда уснуть',
        'лучше не жить',
        'не стоит жить',
        'не стоит продолжать',
        'все равно умру',
        'все равно умрут',
        'лучше умереть чем',
        'смерть лучше',
        'хочу смерти',
        'желаю смерти',
        'хочу чтобы все закончилось',
        'хочу чтобы это закончилось',
        'хочу чтобы все прекратилось',
        'хочу чтобы это прекратилось'
    ]
    
    # Проверяем наличие ключевых фраз
    for phrase in suicidal_phrases:
        if phrase in message_lower:
            return True
    
    return False

def get_suicidal_response():
    """
    Возвращает ответ для пользователя с суицидальными мыслями
    """
    return {
        'message': '''🚨 Это очень серьезная ситуация, и я не могу продолжать работу с вами в рамках SEEE.

Суицидальные мысли — это не просто негативные идеи. Это результат накопления 15-20 негативных убеждений, которые привели к химической реакции в вашем организме. Когда возникают мысли о том, чтобы покончить жизнь самоубийством, это означает, что ваш организм уже находится в критическом состоянии.

**Вам СРОЧНО необходимо обратиться к психиатру** для получения медикаментозного лечения, которое поможет подавить такое поведение организма и стабилизировать ваше состояние.

После того, как психиатр назначит лечение и ваше состояние стабилизируется, вы сможете вернуться к работе с SEEE для проработки тех идей, которые привели к такому состоянию.

**Помните:** медикаментозное лечение необходимо для стабилизации организма, а работа с идеями поможет вам в долгосрочной перспективе.

Если вам нужна срочная помощь, обратитесь:
- Телефон доверия: 8-800-2000-122 (круглосуточно, бесплатно)
- Служба экстренной психологической помощи: 112
- Обратитесь в ближайшую психиатрическую клинику или к частному психиатру

Ваша жизнь важна. Пожалуйста, обратитесь за профессиональной помощью.''',
        'is_critical': True,
        'requires_psychiatrist': True,
        'show_navigation': False,
        'critical': True  # Дополнительный флаг для совместимости
    }

# ============================================
# ЗАДАЧА 3: Разделение физических и эмоциональных последствий
# ============================================

# Определяем порядок полей структуры концепции
CONCEPT_FIELD_ORDER = [
    'goal',  # или 'purpose'
    'parts',  # или 'composition'
    'founder',
    'consequences_emotional',  # НОВОЕ: сначала эмоциональные
    'consequences_physical',   # НОВОЕ: потом физические
    'conclusion'  # или 'conclusions'
]

def ask_consequences_questions(concept, current_field, user_response=None):
    """Обработка вопросов о последствиях с разделением на эмоциональные и физические"""
    
    if current_field == 'consequences_emotional':
        question = "Какие эмоциональные последствия имеет эта идея?"
        # Если есть ответ пользователя, сохраняем
        if user_response is not None:
            if 'consequences' not in concept:
                concept['consequences'] = {'emotional': [], 'physical': []}
            # Обрабатываем ответ - может быть строка или список
            if isinstance(user_response, str):
                # Разделяем по запятым или переносам строк
                emotional_list = [item.strip() for item in user_response.replace('\n', ',').split(',') if item.strip()]
                concept['consequences']['emotional'] = emotional_list
            else:
                concept['consequences']['emotional'] = user_response
        
    elif current_field == 'consequences_physical':
        question = "Какие физические последствия имеет эта идея?"
        # Если есть ответ пользователя, сохраняем
        if user_response is not None:
            if 'consequences' not in concept:
                concept['consequences'] = {'emotional': [], 'physical': []}
            # Обрабатываем ответ
            if isinstance(user_response, str):
                physical_list = [item.strip() for item in user_response.replace('\n', ',').split(',') if item.strip()]
                concept['consequences']['physical'] = physical_list
            else:
                concept['consequences']['physical'] = user_response
    else:
        question = None
    
    return question


# ============================================
# ЗАДАЧА 7: Изменить вопрос после частей концепции
# ============================================

# БЫЛО:
# if current_field == 'parts' and is_complete:
#     question = "Есть ли что-то ещё что вы хотели бы изменить или добавить к этой идее?"

# СТАЛО:
def ask_after_parts_question(concept):
    """Вопрос после заполнения частей концепции - ИЗМЕНЕН"""
    # НОВЫЙ ВОПРОС:
    question = "Есть ли ещё какие-то части этой идеи или идём дальше?"
    return question

def check_parts_completion(concept):
    """Проверяет, завершено ли заполнение частей и нужно ли задать вопрос"""
    parts = concept.get('composition', []) or concept.get('parts', [])
    # Если части есть, задаем вопрос
    if parts:
        return True
    return False

# Также исправить обработку skip_step:
@socketio.on('skip_step')
def handle_skip_step(data):
    """Обработка пропуска шага - ИСПРАВЛЕНА"""
    session_id = data.get('session_id')
    session_data = get_session(session_id)
    current_concept = session_data.get('current_concept') or get_current_concept(session_id)
    
    if not current_concept:
        emit('error', {'message': 'Концепция не найдена'})
        return
    
    current_field = current_concept.get('current_field')
    
    # ЗАДАЧА 3: Специальная обработка для эмоциональных последствий
    # Даже при пропуске переходим к физическим последствиям
    if current_field == 'consequences_emotional':
        next_field = 'consequences_physical'
        current_concept['current_field'] = next_field
        # Инициализируем пустой массив, если его нет
        if 'consequences' not in current_concept:
            current_concept['consequences'] = {'emotional': [], 'physical': []}
        next_question = get_next_question_for_field(next_field, current_concept)
        
        emit('response', {
            'message': next_question,
            'current_field': next_field,
            'show_navigation': True
        })
        save_session(session_id, session_data)
        return
    
    # ИСПРАВЛЕНИЕ: Убрали сообщение "хорошо, пропустим состав"
    if current_field == 'parts' or current_field == 'composition':
        # Просто переходим к следующему полю, без сообщения "пропустим состав"
        next_field = move_to_next_field(session_id, current_concept)
        next_question = get_next_question_for_field(next_field, current_concept)
        
        emit('response', {
            'message': next_question,
            'current_field': next_field,
            'show_navigation': True
        })
    else:
        # Для других полей - стандартная обработка
        next_field = move_to_next_field(session_id, current_concept)
        next_question = get_next_question_for_field(next_field, current_concept)
        
        emit('response', {
            'message': next_question,
            'current_field': next_field,
            'show_navigation': True
        })
    
    save_session(session_id, session_data)


# ============================================
# ЗАДАЧА 8: Изменить вопрос о цели идеи
# ============================================

# БЫЛО:
# if current_field == 'goal' or current_field == 'purpose':
#     question = "С какой целью появилась идея?"

# СТАЛО:
def ask_goal_question():
    """Вопрос о цели появления идеи - ИЗМЕНЕН"""
    # НОВЫЙ ВОПРОС:
    question = "Как вы думаете с какой целью эта идея внедрялась в ваш разум?"
    return question

# Использование в get_next_question_for_field():
# if current_field in ['goal', 'purpose']:
#     question = ask_goal_question()


# ============================================
# НОВЫЕ ОБРАБОТЧИКИ Socket.IO
# ============================================

@socketio.on('update_belief_name')
def handle_update_belief_name(data):
    """Обновление названия убеждения"""
    session_id = data.get('session_id')
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    
    # Получаем сессию из базы данных
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    # Обновляем название
    if old_name in concepts:
        concept = concepts.pop(old_name)
        concept['name'] = new_name
        concepts[new_name] = concept
        
        # Обновляем все ссылки на это убеждение
        update_concept_references(session_id, old_name, new_name)
        
        # Сохраняем в базу
        save_session(session_id, session_data)
        
        emit('response', {
            'message': f'Название убеждения обновлено на "{new_name}"',
            'available_concepts': list(concepts.keys())
        })
    else:
        emit('error', {'message': 'Убеждение не найдено'})


@socketio.on('delete_belief')
def handle_delete_belief(data):
    """Удаление убеждения"""
    session_id = data.get('session_id')
    concept_name = data.get('concept_name')
    
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    if concept_name in concepts:
        del concepts[concept_name]
        save_session(session_id, session_data)
        
        emit('response', {
            'message': f'Убеждение "{concept_name}" удалено',
            'available_concepts': list(concepts.keys())
        })
    else:
        emit('error', {'message': 'Убеждение не найдено'})


@socketio.on('strikethrough_belief')
def handle_strikethrough_belief(data):
    """Зачеркивание убеждения (помечает как неактуальное)"""
    session_id = data.get('session_id')
    concept_name = data.get('concept_name')
    
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    if concept_name in concepts:
        concepts[concept_name]['is_strikethrough'] = True
        save_session(session_id, session_data)
        
        emit('response', {
            'message': f'Убеждение "{concept_name}" помечено как неактуальное',
            'available_concepts': list(concepts.keys())
        })
    else:
        emit('error', {'message': 'Убеждение не найдено'})


@socketio.on('get_concept_full')
def handle_get_concept_full(data):
    """Получение полной структуры концепции"""
    session_id = data.get('session_id')
    concept_name = data.get('concept_name')
    
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    if concept_name in concepts:
        concept = concepts[concept_name]
        
        # Формируем структуру для отправки
        structure = {
            'goal': concept.get('purpose') or concept.get('goal'),
            'parts': concept.get('composition', []),
            'founder': concept.get('founder'),
            'consequences_emotional': concept.get('consequences', {}).get('emotional', []),
            'consequences_physical': concept.get('consequences', {}).get('physical', []),
            'conclusion': concept.get('conclusions')
        }
        
        emit('concept_full_structure', {
            'concept_name': concept_name,
            'structure': structure
        })
    else:
        emit('error', {'message': 'Концепция не найдена'})


@socketio.on('get_concepts_hierarchy')
def handle_get_concepts_hierarchy(data):
    """Получение иерархии концепций для отображения структуры"""
    session_id = data.get('session_id')
    
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    # Строим иерархию на основе extracted_from
    hierarchy = build_concepts_hierarchy(concepts)
    
    emit('concepts_hierarchy', {
        'hierarchy': hierarchy,
        'concepts': concepts
    })


def build_concepts_hierarchy(concepts):
    """
    Строит иерархию концепций на основе связей extracted_from
    Возвращает структуру с уровнями вложенности
    """
    # Находим корневые концепции (те, у которых нет extracted_from)
    root_concepts = []
    child_map = {}  # Карта: родитель -> список детей
    
    for concept_name, concept in concepts.items():
        parent_name = concept.get('extracted_from')
        if parent_name:
            if parent_name not in child_map:
                child_map[parent_name] = []
            child_map[parent_name].append(concept_name)
        else:
            root_concepts.append(concept_name)
    
    # Строим иерархическую структуру
    def build_tree(concept_name, level=0):
        concept = concepts.get(concept_name, {})
        children = child_map.get(concept_name, [])
        
        node = {
            'name': concept_name,
            'level': level,
            'children': [],
            'concept_data': concept
        }
        
        # Рекурсивно добавляем детей
        for child_name in children:
            child_node = build_tree(child_name, level + 1)
            node['children'].append(child_node)
        
        return node
    
    # Строим дерево для каждой корневой концепции
    hierarchy = []
    for root_name in root_concepts:
        hierarchy.append(build_tree(root_name, 0))
    
    # Также добавляем концепции, которые не попали в корневые (на случай циклов)
    processed = set()
    for root_node in hierarchy:
        def mark_processed(node):
            processed.add(node['name'])
            for child in node['children']:
                mark_processed(child)
        mark_processed(root_node)
    
    # Добавляем оставшиеся концепции как корневые
    for concept_name in concepts.keys():
        if concept_name not in processed:
            hierarchy.append(build_tree(concept_name, 0))
    
    return hierarchy


@socketio.on('extract_concept_part')
def handle_extract_concept_part(data):
    """Извлечение части концепции как новой идеи"""
    session_id = data.get('session_id')
    source_concept = data.get('source_concept')
    part_type = data.get('part_type')
    part_value = data.get('part_value')
    
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    if source_concept in concepts:
        # Создаем новую концепцию из части
        new_concept_name = f"{part_value[:50]}"  # Ограничиваем длину
        
        # Создаем базовую структуру новой концепции
        new_concept = {
            'name': new_concept_name,
            'composition': [],
            'founder': None,
            'purpose': None,
            'consequences': {
                'emotional': [],
                'physical': []
            },
            'conclusions': None,
            'comments': [],
            'sub_concepts': [],
            'extracted_from': source_concept,
            'extracted_part': part_type
        }
        
        # В зависимости от типа части, заполняем соответствующее поле
        if part_type == 'goal':
            new_concept['purpose'] = part_value
        elif part_type == 'parts':
            new_concept['composition'] = [part_value] if isinstance(part_value, str) else part_value
        elif part_type == 'founder':
            new_concept['founder'] = part_value
        elif part_type == 'consequences_emotional':
            new_concept['consequences']['emotional'] = [part_value] if isinstance(part_value, str) else part_value
        elif part_type == 'consequences_physical':
            new_concept['consequences']['physical'] = [part_value] if isinstance(part_value, str) else part_value
        elif part_type == 'conclusion':
            new_concept['conclusions'] = part_value
        
        concepts[new_concept_name] = new_concept
        save_session(session_id, session_data)
        
        emit('response', {
            'message': f'Часть идеи извлечена как новая идея: "{new_concept_name}"',
            'available_concepts': list(concepts.keys())
        })
    else:
        emit('error', {'message': 'Исходная концепция не найдена'})


# ============================================
# УЛУЧШЕННАЯ ОБРАБОТКА КОНТЕКСТА ОСНОВАТЕЛЯ
# ============================================

def extract_founder_context(message, current_concept):
    """
    Извлекает информацию об основателе из сообщения пользователя.
    Распознает фразы типа "это не я, а [имя] как основатель"
    """
    import re
    
    # Паттерны для распознавания упоминания основателя
    # Улучшенные паттерны для лучшего распознавания
    founder_patterns = [
        # "это не я, а Вася Якименко как основатель"
        r'это\s+не\s+я.*?а\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?).*?основател',
        # "не я хотел бы, а Вася Якименко, как основатель"
        r'не\s+я\s+хотел.*?а\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?).*?основател',
        # "основатель Вася Якименко"
        r'основател[ьи]\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
        # "Вася Якименко, как основатель"
        r'([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?).*?как\s+основател',
        # "основатель - это Вася Якименко"
        r'основател[ьи].*?это\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
        # "основатель: Вася Якименко"
        r'основател[ьи][:\s]+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
        # "Вася Якименко - основатель"
        r'([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?).*?основател',
    ]
    
    founder_name = None
    for pattern in founder_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            founder_name = match.group(1).strip()
            # Убираем лишние слова, если попались
            founder_name = re.sub(r'\s+(как|это|бы|был|была)\s*$', '', founder_name, flags=re.IGNORECASE)
            break
    
    # Если нашли имя основателя, обновляем концепцию
    if founder_name:
        if current_concept:
            current_concept['founder'] = founder_name
            # Если текущее поле - цель, связываем её с основателем
            current_field = current_concept.get('current_field')
            if current_field in ['goal', 'purpose']:
                purpose_text = current_concept.get('purpose', '')
                # Проверяем, не добавлена ли уже пометка
                if f'основател' not in purpose_text.lower():
                    if purpose_text:
                        current_concept['purpose'] = f"{purpose_text} (цели основателя {founder_name})"
                    else:
                        # Если цели еще нет, сохраняем информацию для следующего шага
                        current_concept['_pending_founder'] = founder_name
        
        return founder_name
    
    return None


def process_message_with_context(message, session_id, current_concept):
    """
    Обрабатывает сообщение с учетом контекста основателя.
    Автоматически связывает цели с основателем, если это указано.
    """
    import re
    
    # Проверяем, упоминается ли основатель
    founder_name = extract_founder_context(message, current_concept)
    
    # Если упоминается основатель и мы работаем с целью
    if founder_name and current_concept:
        current_field = current_concept.get('current_field')
        
        # Проверяем, есть ли в сообщении указание, что цели относятся к основателю
        goals_related_to_founder = any(phrase in message.lower() for phrase in [
            'это не я', 'не я хотел', 'не я хотел бы', 'не я',
            'основатель', 'как основатель', 'основателя'
        ])
        
        # Если текущее поле - цель, уточняем связь
        if current_field in ['goal', 'purpose']:
            if goals_related_to_founder:
                # Обновляем цель с указанием основателя
                purpose_text = current_concept.get('purpose', '')
                # Убираем старые пометки, если есть
                purpose_text = re.sub(r'\s*\(цели основателя[^)]+\)', '', purpose_text)
                if founder_name not in purpose_text:
                    if purpose_text:
                        current_concept['purpose'] = f"{purpose_text} (цели основателя {founder_name})"
                    else:
                        # Если цели еще нет, сохраняем для следующего шага
                        current_concept['_pending_founder'] = founder_name
                    current_concept['founder'] = founder_name
                    
                    return {
                        'message': f'Понял! Цели относятся к основателю {founder_name}. Обновил информацию. Продолжайте описывать цели.',
                        'concept_updated': True,
                        'founder': founder_name,
                        'continue_field': current_field  # Продолжаем заполнение того же поля
                    }
        
        # Если есть сохраненный основатель из предыдущего шага
        if current_concept.get('_pending_founder') and current_field in ['goal', 'purpose']:
            pending_founder = current_concept['_pending_founder']
            purpose_text = current_concept.get('purpose', '')
            if pending_founder not in purpose_text:
                current_concept['purpose'] = f"{purpose_text} (цели основателя {pending_founder})"
            current_concept['founder'] = pending_founder
            del current_concept['_pending_founder']
            
            return {
                'message': f'Связал цели с основателем {pending_founder}.',
                'concept_updated': True,
                'founder': pending_founder
            }
    
    # Если упоминается основатель в контексте исправления
    if founder_name:
        # Проверяем, есть ли указание на исправление
        correction_phrases = [
            'это не', 'не так', 'исправь', 'неправильно',
            'на самом деле', 'правильнее'
        ]
        
        if any(phrase in message.lower() for phrase in correction_phrases):
            if current_concept:
                current_concept['founder'] = founder_name
                return {
                    'message': f'Исправил! Основатель: {founder_name}. Цели теперь связаны с основателем.',
                    'concept_updated': True,
                    'founder': founder_name
                }
    
    return None


@socketio.on('message')
def handle_message(data):
    """Обработка сообщения с улучшенным контекстом и всеми изменениями"""
    session_id = data.get('session_id')
    message = data.get('message', '')
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: Обнаружение суицидальных мыслей
    if detect_suicidal_thoughts(message):
        suicidal_response = get_suicidal_response()
        emit('response', suicidal_response)
        return
    
    # Получаем текущую сессию и концепцию
    session_data = get_session(session_id)
    current_concept = session_data.get('current_concept') or get_current_concept(session_id)
    
    if not current_concept:
        emit('error', {'message': 'Концепция не найдена. Создайте новую сессию.'})
        return
    
    # Обрабатываем сообщение с учетом контекста основателя
    context_result = process_message_with_context(message, session_id, current_concept)
    
    if context_result and context_result.get('concept_updated'):
        # Сохраняем обновленную концепцию
        save_session(session_id, session_data)
        
        # Если нужно продолжить заполнение того же поля
        if context_result.get('continue_field'):
            current_field = context_result.get('continue_field')
            next_question = get_next_question_for_field(current_field, current_concept)
            
            emit('response', {
                'message': f"{context_result['message']}\n\n{next_question}",
                'concept_updated': True,
                'founder': context_result.get('founder'),
                'current_field': current_field,
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
        else:
            emit('response', {
                'message': context_result['message'],
                'concept_updated': True,
                'founder': context_result.get('founder'),
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
        return
    
    # Получаем текущее поле
    current_field = get_current_field(current_concept)
    
    # Проверяем, ожидается ли выбор части идеи для разбора
    if current_concept and current_concept.get('awaiting_part_selection'):
        # Пользователь выбирает часть для разбора
        source_concept_name = current_concept.get('name')
        
        # Определяем выбранную часть
        parts = current_concept.get('composition', []) or current_concept.get('parts', [])
        selected_part_name = None
        
        # Пытаемся найти по номеру
        try:
            part_index = int(message.strip()) - 1
            if 0 <= part_index < len(parts):
                selected_part_name = parts[part_index]
        except (ValueError, TypeError):
            # Если не число, ищем по названию
            selected_part_name = message.strip()
            if selected_part_name not in parts:
                # Ищем частичное совпадение
                for part in parts:
                    if selected_part_name.lower() in part.lower() or part.lower() in selected_part_name.lower():
                        selected_part_name = part
                        break
        
        if not selected_part_name:
            emit('error', {'message': f'Часть "{message}" не найдена. Выберите номер или название из списка.'})
            return
        
        # Проверяем, не пропустил ли пользователь
        if message.lower().strip() in ['пропустить', 'пропустить выбор части', 'далее', 'skip']:
            current_concept['awaiting_part_selection'] = False
            emit('response', {
                'message': 'Отлично! Структура идеи заполнена. Хотите что-то изменить или перейти к другой идее?',
                'current_field': None,
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
            save_session(session_id, session_data)
            return
        
        # Создаем новую концепцию из выбранной части
        concepts = session_data.get('concepts', {})
        new_concept = {
            'name': selected_part_name,
            'composition': [],
            'founder': None,
            'purpose': None,
            'consequences': {
                'emotional': [],
                'physical': []
            },
            'conclusions': None,
            'comments': [],
            'sub_concepts': [],
            'extracted_from': source_concept_name,
            'extracted_part': 'parts'
        }
        
        # Добавляем в список концепций
        concepts[selected_part_name] = new_concept
        
        # Устанавливаем как текущую концепцию
        session_data['current_concept'] = new_concept
        session_data['current_concept_name'] = selected_part_name
        current_concept['awaiting_part_selection'] = False
        
        # Начинаем разбор новой идеи с первого вопроса
        first_field = CONCEPT_FIELD_ORDER[0]
        new_concept['current_field'] = first_field
        first_question = get_next_question_for_field(first_field, new_concept)
        
        save_session(session_id, session_data)
        
        emit('response', {
            'message': f'Отлично! Начинаем разбор части «{selected_part_name}».\n\n{first_question}',
            'current_field': first_field,
            'show_navigation': True,
            'available_concepts': list(concepts.keys()),
            'concept_selected': True
        })
        return
    
    # Обрабатываем ответ пользователя для текущего поля
    if current_field:
        # Сохраняем ответ в концепцию
        process_field_response(current_field, message, current_concept)
        
        # ЗАДАЧА 7: Специальная обработка для частей
        if current_field in ['parts', 'composition']:
            # После ответа о частях задаем новый вопрос
            next_question = ask_after_parts_question(current_concept)
            emit('response', {
                'message': next_question,
                'current_field': current_field,
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
            save_session(session_id, session_data)
            return
        
        # ЗАДАЧА 3: Специальная обработка для эмоциональных последствий
        # После эмоциональных последствий ОБЯЗАТЕЛЬНО переходим к физическим
        if current_field == 'consequences_emotional':
            # Переходим к физическим последствиям
            next_field = 'consequences_physical'
            current_concept['current_field'] = next_field
            next_question = get_next_question_for_field(next_field, current_concept)
            
            emit('response', {
                'message': next_question,
                'current_field': next_field,
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
            save_session(session_id, session_data)
            return
        
        # ЗАДАЧА: После вывода автоматически спрашиваем про части идеи
        if current_field in ['conclusion', 'conclusions']:
            # После вывода задаем вопрос о частях идеи, которые тоже являются идеями
            concept_name = current_concept.get('name', 'эта идея')
            parts = current_concept.get('composition', []) or current_concept.get('parts', [])
            
            if parts:
                # Формируем список частей для выбора
                parts_list = '\n'.join([f"{i+1}. {part}" for i, part in enumerate(parts)])
                next_question = f"У вашей идеи «{concept_name}» есть такие части, которые так же являются идеями и их стоит разобрать. Какую из них вы хотите разобрать сейчас?\n\n{parts_list}"
                
                # Устанавливаем специальное состояние для выбора части
                current_concept['awaiting_part_selection'] = True
                current_concept['current_field'] = None  # Завершили заполнение структуры
                
                emit('response', {
                    'message': next_question,
                    'current_field': None,
                    'show_navigation': True,
                    'available_concepts': list(session_data.get('concepts', {}).keys()),
                    'parts_for_selection': parts,  # Отправляем части для выбора на frontend
                    'awaiting_part_selection': True
                })
            else:
                # Если частей нет, просто завершаем
                emit('response', {
                    'message': 'Отлично! Структура идеи заполнена. Хотите что-то изменить или перейти к другой идее?',
                    'current_field': None,
                    'show_navigation': True,
                    'available_concepts': list(session_data.get('concepts', {}).keys())
                })
            
            save_session(session_id, session_data)
            return
        
        # Для остальных полей переходим к следующему
        next_field = move_to_next_field(session_id, current_concept)
        
        if next_field:
            next_question = get_next_question_for_field(next_field, current_concept)
            emit('response', {
                'message': next_question,
                'current_field': next_field,
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
        else:
            # Все поля заполнены (но не вывод - вывод обработан выше)
            emit('response', {
                'message': 'Отлично! Структура идеи заполнена. Хотите что-то изменить или перейти к другой идее?',
                'current_field': None,
                'show_navigation': True,
                'available_concepts': list(session_data.get('concepts', {}).keys())
            })
    else:
        # Если поля нет, начинаем с первого
        first_field = CONCEPT_FIELD_ORDER[0]
        current_concept['current_field'] = first_field
        first_question = get_next_question_for_field(first_field, current_concept)
        
        emit('response', {
            'message': first_question,
            'current_field': first_field,
            'show_navigation': True,
            'available_concepts': list(session_data.get('concepts', {}).keys())
        })
    
    save_session(session_id, session_data)


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ - ПОЛНАЯ РЕАЛИЗАЦИЯ
# ============================================

def get_current_user_id():
    """
    Получить ID текущего авторизованного пользователя из сессии
    """
    # Получаем user_id из Flask session
    # user_id сохраняется в session при логине/регистрации
    user_id = session.get('user_id')
    
    # Если user_id есть в session, возвращаем его
    if user_id:
        return user_id
    
    # Если нет в session, пробуем получить из заголовков (для API запросов)
    # Некоторые клиенты могут передавать user_id в заголовке
    user_id_header = request.headers.get('X-User-ID')
    if user_id_header:
        try:
            return int(user_id_header)
        except (ValueError, TypeError):
            pass
    
    # Если ничего не найдено, возвращаем None (пользователь не авторизован)
    return None

def get_session(session_id):
    """
    Получить данные сессии из базы данных
    КРИТИЧНО: Проверяет принадлежность сессии пользователю!
    """
    if not session_id:
        return {'concepts': {}, 'current_concept': None, 'current_concept_name': None}
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Получаем данные сессии
        c.execute('SELECT user_id, data FROM sessions WHERE session_id = ?', (str(session_id),))
        row = c.fetchone()
        
        if not row:
            conn.close()
            # Если сессии нет, возвращаем пустую структуру
            return {'concepts': {}, 'current_concept': None, 'current_concept_name': None}
        
        session_user_id, data_json = row
        
        # КРИТИЧНО: Проверяем принадлежность сессии
        current_user_id = get_current_user_id()
        if current_user_id and current_user_id != session_user_id:
            conn.close()
            raise PermissionError("Доступ запрещен: сессия принадлежит другому пользователю")
        
        # Парсим JSON данные
        if data_json:
            try:
                session_data = json.loads(data_json)
            except json.JSONDecodeError:
                session_data = {'concepts': {}, 'current_concept': None, 'current_concept_name': None}
        else:
            session_data = {'concepts': {}, 'current_concept': None, 'current_concept_name': None}
        
        conn.close()
        return session_data
        
    except Exception as e:
        conn.close()
        # В случае ошибки возвращаем пустую структуру
        return {'concepts': {}, 'current_concept': None, 'current_concept_name': None}

def save_session(session_id, session_data):
    """
    Сохранить данные сессии в базу данных
    КРИТИЧНО: Проверяет принадлежность сессии пользователю!
    """
    if not session_id:
        return
    
    # Получаем ID текущего пользователя
    user_id = get_current_user_id()
    if not user_id:
        # Если пользователь не авторизован, не сохраняем сессию
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Проверяем, существует ли уже сессия
        c.execute('SELECT user_id FROM sessions WHERE session_id = ?', (str(session_id),))
        existing = c.fetchone()
        
        if existing:
            # КРИТИЧНО: Проверяем принадлежность сессии
            if existing[0] != user_id:
                conn.close()
                raise PermissionError("Доступ запрещен: сессия принадлежит другому пользователю")
            
            # Обновляем существующую сессию
            data_json = json.dumps(session_data, ensure_ascii=False)
            c.execute('''UPDATE sessions 
                         SET data = ?, updated_at = CURRENT_TIMESTAMP 
                         WHERE session_id = ?''', 
                     (data_json, str(session_id)))
        else:
            # Создаем новую сессию
            data_json = json.dumps(session_data, ensure_ascii=False)
            c.execute('''INSERT INTO sessions (user_id, session_id, data) 
                         VALUES (?, ?, ?)''', 
                     (user_id, str(session_id), data_json))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        conn.close()
        # Логируем ошибку, но не прерываем выполнение
        print(f"Ошибка сохранения сессии: {e}")

def get_current_concept(session_id):
    """Получить текущую концепцию из сессии"""
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    current_concept_name = session_data.get('current_concept_name')
    if current_concept_name and current_concept_name in concepts:
        return concepts[current_concept_name]
    return None

def get_current_field(concept):
    """Получить текущее поле, которое заполняется"""
    if not concept:
        return None
    return concept.get('current_field')

def move_to_next_field(session_id, concept):
    """Переход к следующему полю структуры концепции"""
    if not concept:
        return None
    
    current_field = concept.get('current_field')
    if not current_field:
        # Если поля нет, начинаем с первого
        concept['current_field'] = CONCEPT_FIELD_ORDER[0]
        return CONCEPT_FIELD_ORDER[0]
    
    # ЗАДАЧА 3: Специальная обработка для эмоциональных последствий
    # После эмоциональных ОБЯЗАТЕЛЬНО переходим к физическим
    if current_field == 'consequences_emotional':
        next_field = 'consequences_physical'
        concept['current_field'] = next_field
        return next_field
    
    # Находим текущее поле в порядке
    try:
        current_index = CONCEPT_FIELD_ORDER.index(current_field)
    except ValueError:
        # Если поле не найдено, пробуем найти альтернативные названия
        field_mapping = {
            'purpose': 'goal',
            'composition': 'parts',
            'conclusions': 'conclusion'
        }
        mapped_field = field_mapping.get(current_field, current_field)
        try:
            current_index = CONCEPT_FIELD_ORDER.index(mapped_field)
            current_field = mapped_field
        except ValueError:
            # Если все равно не найдено, начинаем сначала
            concept['current_field'] = CONCEPT_FIELD_ORDER[0]
            return CONCEPT_FIELD_ORDER[0]
    
    # Переходим к следующему полю
    if current_index < len(CONCEPT_FIELD_ORDER) - 1:
        next_field = CONCEPT_FIELD_ORDER[current_index + 1]
        concept['current_field'] = next_field
        return next_field
    else:
        # Все поля заполнены
        concept['current_field'] = None
        concept['is_complete'] = True
        return None

def get_next_question_for_field(field, concept):
    """Получить вопрос для конкретного поля"""
    if not field:
        return "Все поля заполнены. Хотите что-то изменить?"
    
    # ЗАДАЧА 8: Измененный вопрос о цели
    if field in ['goal', 'purpose']:
        return ask_goal_question()
    
    # ЗАДАЧА 7: Измененный вопрос после частей
    elif field in ['parts', 'composition']:
        # Проверяем, есть ли уже части
        parts = concept.get('composition', []) or concept.get('parts', [])
        if parts:
            # Если части уже есть, задаем новый вопрос
            return ask_after_parts_question(concept)
        else:
            # Если частей нет, задаем первый вопрос
            return "Из каких частей состоит эта идея?"
    
    elif field == 'founder':
        return "Кто является основателем этой идеи? (Кому было выгодно, чтобы такая идея у вас появилась?)"
    
    # ЗАДАЧА 3: Разделение последствий
    elif field == 'consequences_emotional':
        return ask_consequences_questions(concept, field)
    
    elif field == 'consequences_physical':
        return ask_consequences_questions(concept, field)
    
    elif field in ['conclusion', 'conclusions']:
        return "Какой вывод можно сделать об этой идее?"
    
    return "Продолжаем работу с этой идеей."

def process_field_response(field, user_response, concept):
    """Обработать ответ пользователя для конкретного поля"""
    if not concept:
        return False
    
    # Обработка ответа в зависимости от поля
    if field in ['goal', 'purpose']:
        concept['purpose'] = user_response
        # Если был сохранен основатель, связываем
        if concept.get('_pending_founder'):
            founder = concept['_pending_founder']
            concept['purpose'] = f"{user_response} (цели основателя {founder})"
            concept['founder'] = founder
            del concept['_pending_founder']
    
    elif field in ['parts', 'composition']:
        # Обрабатываем части - могут быть через запятую или список
        if isinstance(user_response, str):
            parts_list = [item.strip() for item in user_response.replace('\n', ',').split(',') if item.strip()]
            concept['composition'] = parts_list
        else:
            concept['composition'] = user_response
    
    elif field == 'founder':
        concept['founder'] = user_response
    
    # ЗАДАЧА 3: Разделение последствий
    elif field == 'consequences_emotional':
        ask_consequences_questions(concept, field, user_response)
    
    elif field == 'consequences_physical':
        ask_consequences_questions(concept, field, user_response)
    
    elif field in ['conclusion', 'conclusions']:
        concept['conclusions'] = user_response
    
    return True

def update_concept_references(session_id, old_name, new_name):
    """Обновить все ссылки на концепцию при переименовании"""
    session_data = get_session(session_id)
    concepts = session_data.get('concepts', {})
    
    # Обновляем ссылки в других концепциях
    for concept_name, concept in concepts.items():
        # Проверяем sub_concepts
        if 'sub_concepts' in concept:
            for i, sub_concept in enumerate(concept['sub_concepts']):
                if sub_concept == old_name:
                    concept['sub_concepts'][i] = new_name
        
        # Проверяем extracted_from
        if concept.get('extracted_from') == old_name:
            concept['extracted_from'] = new_name
    
    save_session(session_id, session_data)


# ============================================
# АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ
# ============================================

def init_db():
    """Инициализация базы данных - создание таблиц если их нет"""
    conn = get_db()
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        user_id TEXT UNIQUE,
        referral_code TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица сессий (для хранения данных сессий работы с идеями)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id TEXT UNIQUE NOT NULL,
        data TEXT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Добавляем колонку title если её нет (для существующих БД)
    try:
        c.execute('ALTER TABLE sessions ADD COLUMN title TEXT')
    except sqlite3.OperationalError:
        pass  # Колонка уже существует
    
    # Таблица рефералов (для MLM системы)
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER NOT NULL,
        referred_id INTEGER NOT NULL,
        level INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referrer_id) REFERENCES users(id),
        FOREIGN KEY (referred_id) REFERENCES users(id),
        UNIQUE(referrer_id, referred_id, level)
    )''')
    
    # Таблица балансов
    c.execute('''CREATE TABLE IF NOT EXISTS balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        amount REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Таблица транзакций
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        referral_level INTEGER,
        from_user_id INTEGER,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (from_user_id) REFERENCES users(id)
    )''')
    
    # Таблица журнала сессий
    c.execute('''CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id INTEGER,
        session_title TEXT,
        feeling_after TEXT,
        emotion_after TEXT,
        how_session_went TEXT,
        interesting_thoughts TEXT,
        date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Таблица интересных мыслей
    c.execute('''CREATE TABLE IF NOT EXISTS thoughts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id INTEGER,
        thought_number INTEGER,
        title TEXT,
        thought_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Таблица реквизитов для выплат
    c.execute('''CREATE TABLE IF NOT EXISTS payment_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        full_name TEXT,
        phone TEXT,
        bank_name TEXT,
        account_number TEXT,
        bik TEXT,
        inn TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Таблица безопасности пользователя
    c.execute('''CREATE TABLE IF NOT EXISTS user_security (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        email TEXT,
        two_factor_enabled BOOLEAN DEFAULT 0,
        two_factor_secret TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Таблица контактов пользователя (для уведомлений)
    c.execute('''CREATE TABLE IF NOT EXISTS user_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        email TEXT,
        telegram TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Проверка пароля"""
    return hash_password(password) == password_hash

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # POST запрос - обработка регистрации
    data = request.json if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    referrer_code = data.get('referrer_code', '').strip() or None
    
    # Валидация
    if not username or len(username) < 3:
        return jsonify({'success': False, 'error': 'Имя пользователя должно содержать минимум 3 символа'}), 400
    
    if not password or len(password) < 3:
        return jsonify({'success': False, 'error': 'Пароль должен содержать минимум 3 символа'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Проверяем, не существует ли уже такой пользователь
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь с таким именем уже существует'}), 400
        
        # Генерируем уникальный user_id
        import uuid
        user_id_str = str(uuid.uuid4())
        
        # Генерируем реферальный код
        referral_code = generate_referral_code()
        
        # Хешируем пароль
        password_hash = hash_password(password)
        
        # Создаем пользователя
        c.execute('''INSERT INTO users (username, password_hash, user_id, referral_code) 
                     VALUES (?, ?, ?, ?)''', 
                 (username, password_hash, user_id_str, referral_code))
        
        user_db_id = c.lastrowid
        conn.commit()
        
        # Создаем реферальную структуру
        if referrer_code:
            create_referral_structure(user_db_id, referrer_code)
        
        # Сохраняем user_id в сессию
        session['user_id'] = user_db_id
        session['username'] = username
        session['user_id_str'] = user_id_str
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Регистрация успешна',
            'user_id': user_db_id
        })
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Ошибка регистрации. Попробуйте другое имя пользователя'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': f'Ошибка регистрации: {str(e)}'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход пользователя"""
    if request.method == 'GET':
        # Если пользователь уже авторизован, перенаправляем на главную
        if session.get('user_id'):
            return redirect(url_for('index'))
        return render_template('login.html') if os.path.exists('templates/login.html') else jsonify({'error': 'Страница логина не найдена'}), 404
    
    # POST запрос - обработка входа
    data = request.json if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Введите имя пользователя и пароль'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Ищем пользователя
    c.execute('SELECT id, password_hash, user_id, username FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'error': 'Неверное имя пользователя или пароль'}), 401
    
    user_id, password_hash, user_id_str, db_username = user
    
    # Проверяем пароль
    if not verify_password(password, password_hash):
        return jsonify({'success': False, 'error': 'Неверное имя пользователя или пароль'}), 401
    
    # Сохраняем user_id в сессию
    session['user_id'] = user_id
    session['username'] = db_username
    session['user_id_str'] = user_id_str
    
    return jsonify({
        'success': True,
        'message': 'Вход выполнен успешно',
        'user_id': user_id
    })

@app.route('/logout', methods=['POST'])
def logout():
    """Выход пользователя"""
    session.clear()
    return jsonify({'success': True, 'message': 'Выход выполнен'})

@app.route('/')
def index():
    """Главная страница"""
    try:
        # Используем index.html как основной шаблон
        template_name = 'index.html'
        template_path = os.path.join(templates_dir, template_name)
        
        if os.path.exists(template_path):
            return render_template(template_name)
    except Exception as e:
        print(f"Ошибка при рендеринге шаблона: {e}")
        import traceback
        traceback.print_exc()
    
    # Если шаблон не найден, возвращаем простую HTML страницу
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SEEE - Архитектура мышления</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <h1>SEEE - Архитектура мышления</h1>
        <p>Приложение запущено. Главная страница находится в разработке.</p>
        <p><a href="/register">Регистрация</a></p>
        <p><a href="/map">Нейрокарта</a></p>
    </body>
    </html>
    '''

@app.after_request
def inject_centering_script(response):
    """Добавляем скрипты исправления во все HTML ответы"""
    if response.content_type and 'text/html' in response.content_type:
        try:
            # Подключаем fix_all_issues.js
            script_path = os.path.join(os.path.dirname(__file__), 'static', 'js', 'fix_all_issues.js')
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                response_data = response.get_data(as_text=True)
                if '</body>' in response_data and 'fix_all_issues' not in response_data.lower():
                    response_data = response_data.replace('</body>', f'<script>{script_content}</script></body>')
                    response.set_data(response_data)
            
            # Также подключаем inline_center.js
            inline_path = os.path.join(os.path.dirname(__file__), 'static', 'js', 'inline_center.js')
            if os.path.exists(inline_path):
                with open(inline_path, 'r', encoding='utf-8') as f:
                    inline_content = f.read()
                response_data = response.get_data(as_text=True)
                if '</body>' in response_data and 'inline_center' not in response_data.lower():
                    response_data = response_data.replace('</body>', f'<script>{inline_content}</script></body>')
                    response.set_data(response_data)
        except Exception as e:
            print(f"Error injecting scripts: {e}")
    return response

# Инициализируем БД при запуске
init_db()


# ============================================
# API ENDPOINTS ДЛЯ ПОДПИСОК
# ============================================

@app.route('/api/subscription/save-contacts', methods=['POST'])
def save_subscription_contacts():
    """Сохранить контактные данные перед оплатой"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    telegram_username = data.get('telegram', '').strip()
    email = data.get('email', '').strip()
    
    # Валидация
    if not telegram_username:
        return jsonify({'error': 'Укажите Telegram username'}), 400
    
    if not telegram_username.startswith('@'):
        return jsonify({'error': 'Telegram username должен начинаться с @'}), 400
    
    if not email or '@' not in email:
        return jsonify({'error': 'Укажите корректный email'}), 400
    
    # Сохраняем контактную информацию
    save_user_contact_info(user_id, telegram_username, email)
    
    return jsonify({'success': True, 'message': 'Контактные данные сохранены'})

# ============================================
# API ENDPOINTS ДЛЯ ЛИЧНОГО КАБИНЕТА
# ============================================

@app.route('/api/cabinet/info', methods=['GET'])
def get_cabinet_info():
    """Получить информацию для личного кабинета"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Получаем данные пользователя
        c.execute('SELECT username, user_id, referral_code FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        username, user_id_str, referral_code = user
        
        # Формируем реферальную ссылку
        referral_link = f"https://seee-a.up.railway.app/register?ref={referral_code}"
        
        # Получаем рефералов по уровням
        referrals_by_level = {}
        for level in range(1, 9):
            c.execute('''SELECT COUNT(*) FROM referrals 
                        WHERE referrer_id = ? AND level = ?''', (user_id, level))
            count = c.fetchone()[0]
            referrals_by_level[level] = count
        
        # Получаем язык пользователя (если есть в БД)
        language = 'ru'  # По умолчанию
        
        conn.close()
        
        return jsonify({
            'username': username,
            'user_id': user_id_str,
            'referral_code': referral_code,
            'referral_link': referral_link,
            'referrals_by_level': referrals_by_level,
            'language': language
        })
    except Exception as e:
        conn.close()
        print(f"Ошибка получения данных кабинета: {e}")
        return jsonify({'error': 'Ошибка загрузки данных'}), 500

@app.route('/api/cabinet/balance', methods=['GET'])
def get_cabinet_balance():
    """Получить баланс и транзакции"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        from mlm_system import get_user_balance, get_user_transactions
        
        balance = get_user_balance(user_id)
        transactions = get_user_transactions(user_id, limit=50)
        
        return jsonify({
            'balance': balance,
            'transactions': transactions
        })
    except Exception as e:
        print(f"Ошибка получения баланса: {e}")
        return jsonify({'error': 'Ошибка загрузки баланса'}), 500

@app.route('/api/cabinet/journal', methods=['GET'])
def get_cabinet_journal():
    """Получить журнал сессий"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Получаем записи журнала (если есть таблица journal)
        # Пока возвращаем пустой список, если таблицы нет
        c.execute('''SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='journal' ''')
        if c.fetchone():
            c.execute('''SELECT id, session_id, session_title, feeling_after, emotion_after, 
                        how_session_went, interesting_thoughts, date_time
                        FROM journal WHERE user_id = ? ORDER BY date_time DESC''', (user_id,))
            rows = c.fetchall()
            entries = []
            for row in rows:
                entries.append({
                    'id': row[0],
                    'session_id': row[1],
                    'session_title': row[2] or 'Без названия',
                    'feeling_after': row[3],
                    'emotion_after': row[4],
                    'how_session_went': row[5],
                    'interesting_thoughts': row[6],
                    'date_time': row[7]
                })
            conn.close()
            return jsonify({'entries': entries})
        else:
            conn.close()
            return jsonify({'entries': []})
    except Exception as e:
        conn.close()
        print(f"Ошибка получения журнала: {e}")
        return jsonify({'entries': []})

@app.route('/api/cabinet/thoughts', methods=['GET'])
def get_cabinet_thoughts():
    """Получить интересные мысли"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Проверяем наличие таблицы thoughts
        c.execute('''SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='thoughts' ''')
        if c.fetchone():
            c.execute('''SELECT id, session_id, thought_number, title, thought_text, created_at
                        FROM thoughts WHERE user_id = ? ORDER BY thought_number ASC''', (user_id,))
            rows = c.fetchall()
            thoughts = []
            for row in rows:
                thoughts.append({
                    'id': row[0],
                    'session_id': row[1],
                    'thought_number': row[2],
                    'title': row[3] or 'Без названия',
                    'thought_text': row[4] or '',
                    'created_at': row[5]
                })
            conn.close()
            return jsonify({'thoughts': thoughts})
        else:
            conn.close()
            return jsonify({'thoughts': []})
    except Exception as e:
        conn.close()
        print(f"Ошибка получения мыслей: {e}")
        return jsonify({'thoughts': []})

@app.route('/api/cabinet/thoughts', methods=['POST'])
def create_thought():
    """Создать интересную мысль"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    title = data.get('title', '').strip()
    thought_text = data.get('thought_text', '').strip()
    
    if not title and not thought_text:
        return jsonify({'error': 'Укажите название или текст мысли'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Создаем таблицу если её нет
        c.execute('''CREATE TABLE IF NOT EXISTS thoughts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER,
            thought_number INTEGER,
            title TEXT,
            thought_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        # Получаем следующий номер мысли
        c.execute('SELECT MAX(thought_number) FROM thoughts WHERE user_id = ?', (user_id,))
        max_num = c.fetchone()[0]
        thought_number = (max_num or 0) + 1
        
        # Вставляем мысль
        c.execute('''INSERT INTO thoughts (user_id, session_id, thought_number, title, thought_text)
                    VALUES (?, ?, ?, ?, ?)''',
                (user_id, session_id, thought_number, title, thought_text))
        
        thought_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': thought_id, 'thought_number': thought_number})
    except Exception as e:
        conn.close()
        print(f"Ошибка создания мысли: {e}")
        return jsonify({'error': 'Ошибка создания мысли'}), 500

@app.route('/api/cabinet/thoughts/<int:thought_id>', methods=['PUT'])
def update_thought(thought_id):
    """Обновить интересную мысль"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    title = data.get('title', '').strip()
    thought_text = data.get('thought_text', '').strip()
    thought_number = data.get('thought_number')
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Проверяем владельца
        c.execute('SELECT user_id FROM thoughts WHERE id = ?', (thought_id,))
        owner = c.fetchone()
        if not owner or owner[0] != user_id:
            conn.close()
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        # Обновляем
        updates = []
        params = []
        if title:
            updates.append('title = ?')
            params.append(title)
        if thought_text:
            updates.append('thought_text = ?')
            params.append(thought_text)
        if thought_number:
            updates.append('thought_number = ?')
            params.append(thought_number)
        
        if updates:
            params.append(thought_id)
            c.execute(f'UPDATE thoughts SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        print(f"Ошибка обновления мысли: {e}")
        return jsonify({'error': 'Ошибка обновления мысли'}), 500

@app.route('/api/cabinet/payment-details', methods=['GET'])
def get_payment_details():
    """Получить реквизиты для выплат"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Проверяем наличие таблицы payment_details
        c.execute('''SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='payment_details' ''')
        if c.fetchone():
            c.execute('''SELECT full_name, phone, bank_name, account_number, bik, inn
                        FROM payment_details WHERE user_id = ?''', (user_id,))
            row = c.fetchone()
            if row:
                conn.close()
                return jsonify({
                    'full_name': row[0] or '',
                    'phone': row[1] or '',
                    'bank_name': row[2] or '',
                    'account_number': row[3] or '',
                    'bik': row[4] or '',
                    'inn': row[5] or ''
                })
        
        conn.close()
        return jsonify({
            'full_name': '',
            'phone': '',
            'bank_name': '',
            'account_number': '',
            'bik': '',
            'inn': ''
        })
    except Exception as e:
        conn.close()
        print(f"Ошибка получения реквизитов: {e}")
        return jsonify({
            'full_name': '',
            'phone': '',
            'bank_name': '',
            'account_number': '',
            'bik': '',
            'inn': ''
        })

@app.route('/api/cabinet/payment-details', methods=['POST'])
def save_payment_details():
    """Сохранить реквизиты для выплат"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    bank_name = data.get('bank_name', '').strip()
    account_number = data.get('account_number', '').strip()
    bik = data.get('bik', '').strip()
    inn = data.get('inn', '').strip()
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Создаем таблицу если её нет
        c.execute('''CREATE TABLE IF NOT EXISTS payment_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            full_name TEXT,
            phone TEXT,
            bank_name TEXT,
            account_number TEXT,
            bik TEXT,
            inn TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        # Сохраняем или обновляем
        c.execute('''INSERT OR REPLACE INTO payment_details 
                    (user_id, full_name, phone, bank_name, account_number, bik, inn, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                (user_id, full_name, phone, bank_name, account_number, bik, inn))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Реквизиты сохранены'})
    except Exception as e:
        conn.close()
        print(f"Ошибка сохранения реквизитов: {e}")
        return jsonify({'error': 'Ошибка сохранения реквизитов'}), 500

@app.route('/api/cabinet/security/email', methods=['GET', 'POST'])
def handle_security_email():
    """Получить или сохранить email для безопасности"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        if request.method == 'GET':
            # Получаем email
            c.execute('''SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='user_security' ''')
            if c.fetchone():
                c.execute('SELECT email FROM user_security WHERE user_id = ?', (user_id,))
                row = c.fetchone()
                email = row[0] if row else ''
            else:
                email = ''
            
            conn.close()
            return jsonify({'email': email})
        else:
            # Сохраняем email
            data = request.json
            email = data.get('email', '').strip()
            
            # Создаем таблицу если её нет
            c.execute('''CREATE TABLE IF NOT EXISTS user_security (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                email TEXT,
                two_factor_enabled BOOLEAN DEFAULT 0,
                two_factor_secret TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')
            
            c.execute('''INSERT OR REPLACE INTO user_security 
                        (user_id, email, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)''',
                    (user_id, email))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Email сохранен'})
    except Exception as e:
        conn.close()
        print(f"Ошибка работы с email: {e}")
        return jsonify({'error': 'Ошибка работы с email'}), 500

@app.route('/api/cabinet/security/2fa/status', methods=['GET'])
def get_2fa_status():
    """Получить статус 2FA"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('''SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='user_security' ''')
        if c.fetchone():
            c.execute('SELECT two_factor_enabled FROM user_security WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            enabled = bool(row[0]) if row and row[0] else False
        else:
            enabled = False
        
        conn.close()
        return jsonify({'enabled': enabled})
    except Exception as e:
        conn.close()
        print(f"Ошибка получения статуса 2FA: {e}")
        return jsonify({'enabled': False})

@app.route('/api/cabinet/security/2fa/disable', methods=['POST'])
def disable_2fa():
    """Отключить 2FA"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('''UPDATE user_security 
                    SET two_factor_enabled = 0, two_factor_secret = NULL 
                    WHERE user_id = ?''', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '2FA отключена'})
    except Exception as e:
        conn.close()
        print(f"Ошибка отключения 2FA: {e}")
        return jsonify({'error': 'Ошибка отключения 2FA'}), 500

@app.route('/api/cabinet/subscription', methods=['GET'])
def get_cabinet_subscription():
    """Получить информацию о подписке"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        from subscription_system import check_subscription_status, get_user_active_promo
        
        status = check_subscription_status(user_id)
        active_promo = get_user_active_promo(user_id)
        
        # Получаем контакты для уведомлений
        conn = get_db()
        c = conn.cursor()
        
        # Проверяем наличие таблицы user_contacts
        notification_email = ''
        notification_telegram = ''
        
        c.execute('''SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='user_contacts' ''')
        if c.fetchone():
            c.execute('SELECT email, telegram FROM user_contacts WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            if row:
                notification_email = row[0] or ''
                notification_telegram = row[1] or ''
        
        conn.close()
        
        return jsonify({
            'is_active': status['is_active'] or status.get('has_lifetime_promo', False),
            'status_text': 'Платный режим' if (status['is_active'] or status.get('has_lifetime_promo', False)) else 'Бесплатный режим',
            'end_date': status['subscription_end_date'],
            'sessions_used': status['sessions_used'],
            'sessions_limit': status['sessions_limit'],
            'neurocard_completed': status['neurocard_completed'],
            'active_promo_code': active_promo,
            'promo_type': None,
            'notification_email': notification_email,
            'notification_telegram': notification_telegram
        })
    except Exception as e:
        print(f"Ошибка получения подписки: {e}")
        return jsonify({
            'is_active': False,
            'status_text': 'Бесплатный режим',
            'end_date': None,
            'sessions_used': 0,
            'sessions_limit': 2,
            'neurocard_completed': False,
            'active_promo_code': None,
            'promo_type': None,
            'notification_email': '',
            'notification_telegram': ''
        })

@app.route('/api/subscription/apply-promo', methods=['POST'])
def apply_promo():
    """Применить промокод"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    promo_code = data.get('promo_code', '').strip().upper()
    
    if not promo_code:
        return jsonify({'error': 'Укажите промокод'}), 400
    
    try:
        from subscription_system import apply_promo_code
        result = apply_promo_code(user_id, promo_code)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'type': result.get('type')
            })
        else:
            return jsonify({'error': result['error']}), 400
    except Exception as e:
        print(f"Ошибка применения промокода: {e}")
        return jsonify({'error': 'Ошибка применения промокода'}), 500

@app.route('/api/sessions', methods=['GET', 'POST'])
def handle_sessions():
    """Получить список сессий (GET) или создать новую сессию (POST)"""
    if request.method == 'GET':
        user_id = get_current_user_id()
        
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        conn = get_db()
        c = conn.cursor()
        
        try:
            c.execute('''SELECT id, session_id, title, created_at, updated_at 
                        FROM sessions 
                        WHERE user_id = ? 
                        ORDER BY updated_at DESC 
                        LIMIT 50''', (user_id,))
            rows = c.fetchall()
            
            sessions = []
            for row in rows:
                sessions.append({
                    'id': row[0],
                    'session_id': row[1],
                    'title': row[2] or 'Без названия',
                    'created_at': row[3],
                    'updated_at': row[4]
                })
            
            conn.close()
            return jsonify({'sessions': sessions})
        except Exception as e:
            conn.close()
            print(f"Ошибка получения сессий: {e}")
            return jsonify({'sessions': []})
    
    # POST - создание новой сессии
    return create_session()

def create_session():
    """Создать новую сессию"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    title = data.get('title', 'Новая сессия')
    source_thought_id = data.get('source_thought_id')
    initial_message = data.get('initial_message')
    
    # Генерируем уникальный session_id
    import uuid
    session_id = str(uuid.uuid4())
    
    # Создаем начальные данные сессии
    session_data = {
        'concepts': {},
        'current_concept': None,
        'current_concept_name': None,
        'title': title
    }
    
    if initial_message:
        session_data['initial_message'] = initial_message
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Сохраняем сессию в БД
        c.execute('''INSERT INTO sessions (user_id, session_id, data, title)
                    VALUES (?, ?, ?, ?)''',
                (user_id, session_id, json.dumps(session_data), title))
        
        session_db_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': session_db_id,
            'session_id': session_id,
            'title': title
        })
    except Exception as e:
        conn.close()
        print(f"Ошибка создания сессии: {e}")
        return jsonify({'error': 'Ошибка создания сессии'}), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Получить информацию о сессии"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('''SELECT id, data, title FROM sessions 
                    WHERE session_id = ? AND user_id = ?''', 
                (session_id, user_id))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'error': 'Сессия не найдена'}), 404
        
        session_db_id, data_json, title = row
        data = json.loads(data_json) if data_json else {}
        
        conn.close()
        
        return jsonify({
            'id': session_db_id,
            'session_id': session_id,
            'title': title or data.get('title', 'Новая сессия'),
            'data': data
        })
    except Exception as e:
        conn.close()
        print(f"Ошибка получения сессии: {e}")
        return jsonify({'error': 'Ошибка получения сессии'}), 500

@app.route('/api/cabinet/language', methods=['POST'])
def save_language():
    """Сохранить язык интерфейса"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    language = data.get('language', 'ru')
    
    # Можно сохранить в БД, пока просто возвращаем успех
    return jsonify({'success': True, 'message': 'Язык сохранен'})

