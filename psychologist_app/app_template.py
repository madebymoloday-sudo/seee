"""
Шаблон app.py с необходимыми изменениями для задач 3, 7, 8
Этот файл показывает, какие изменения нужно внести в ваш app.py
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

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
    КРИТИЧНО: Получить ID текущего авторизованного пользователя
    Замените на вашу систему авторизации (Flask-Login, JWT, session и т.д.)
    """
    # Пример для Flask-Login:
    # from flask_login import current_user
    # if current_user.is_authenticated:
    #     return current_user.id
    
    # Пример для session:
    # return session.get('user_id')
    
    # Пример для JWT:
    # token = request.headers.get('Authorization', '').replace('Bearer ', '')
    # payload = decode_jwt(token)
    # return payload.get('user_id')
    
    # ВРЕМЕННО: Возвращаем None, но это нужно исправить!
    return None

def get_session(session_id):
    """
    Получить данные сессии из базы данных
    КРИТИЧНО: Должна проверять принадлежность сессии пользователю!
    """
    # TODO: Реализуйте получение данных сессии из вашей БД
    # Пример:
    # from your_db_module import get_session_data, get_session_user_id
    # 
    # # КРИТИЧНО: Проверяем принадлежность сессии
    # user_id = get_current_user_id()
    # session_user_id = get_session_user_id(session_id)
    # 
    # if user_id != session_user_id:
    #     raise PermissionError("Доступ запрещен: сессия принадлежит другому пользователю")
    # 
    # return get_session_data(session_id)
    pass

def save_session(session_id, session_data):
    """
    Сохранить данные сессии в базу данных
    КРИТИЧНО: Должна проверять принадлежность сессии пользователю!
    """
    # TODO: Реализуйте сохранение данных сессии в вашу БД
    # Пример:
    # from your_db_module import save_session_data, get_session_user_id
    # 
    # # КРИТИЧНО: Проверяем принадлежность сессии
    # user_id = get_current_user_id()
    # session_user_id = get_session_user_id(session_id)
    # 
    # if user_id != session_user_id:
    #     raise PermissionError("Доступ запрещен: сессия принадлежит другому пользователю")
    # 
    # save_session_data(session_id, session_data)
    pass

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

