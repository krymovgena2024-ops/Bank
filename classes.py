import random
import requests  # <<< ВОТ ЭТУ СТРОКУ НУЖНО ДОБАВИТЬ!
import sqlite3
from database.database import get_db_path


class BankAccount:
    def __init__(self, account_number, owner_name, age, bank_name):
        self.account_number = account_number  # Внутренний ID из базы данных
        self.owner_name = owner_name
        self.age = age
        self.bank_name = bank_name
        # Генерацию случайного 16-значного номера real_account_card оставляем здесь
        self.real_account_card = "".join([str(random.randint(0, 9)) for _ in range(15)])


class Bank:
    def __init__(self, bank_name):
        self.bank_name = bank_name.title()


    def transfer(self, from_acc_num, to_acc_num, amount, what_to_convert, what_to_convert_into):
        # Теперь оба счета ищутся по длинным номерам через find_account!
        sender = self.find_account(from_acc_num)
        receiver = self.find_account(to_acc_num)
        
        if sender is None:
            print(f"Ошибка: Счет отправителя '{from_acc_num}' не найден.")
            return False
        if receiver is None:
            print(f"Ошибка: Счет получателя '{to_acc_num}' не найден.")
            return False

        # ВАЖНО: Для SQL-запросов списания и зачисления денег нам нужны их внутренние ID.
        # Поскольку метод find_account возвращает объект BankAccount, 
        # внутренний ID теперь лежит в sender.account_number!
        sender_id = sender.account_number
        receiver_id = receiver.account_number

        db_path = get_db_path()
        sender_balance = 0.0
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # Ищем баланс по системному ID отправителя
                cursor.execute("""
                    SELECT balance FROM users_balances 
                    WHERE account_id = ? AND currency = ?
                """, (sender_id, what_to_convert.upper()))
                row = cursor.fetchone()
                if row:
                    sender_balance = row[0]
                else:
                    print(f"Ошибка: У отправителя нет кошелька в валюте {what_to_convert}!")
                    return False
        except Exception as e:
            print(f"Ошибка проверки баланса отправителя: {e}")
            return False

        # расчет комиссии (снимается в валюте отправления) с округлением до 2 знаков
        comission = 0
        if sender.bank_name != receiver.bank_name:
            comission = round(amount * 0.01, 2)  # Округляем до сотых долей
            
        total_amount_to_deduct = amount + comission
        
        # Проверка баланса отправителя
        if sender_balance < total_amount_to_deduct:
            print(f"Недостаточно средств. Требуется: {total_amount_to_deduct} {what_to_convert}, на счету: {sender_balance} {what_to_convert}")
            return False

        # Вызываем конвертацию для получателя
        conversion_result = convert_currency(what_to_convert, what_to_convert_into, amount)

        # ДОБАВЬ ЭТУ ПРОВЕРКУ: Если конвертация не удалась, останавливаем перевод!
        if conversion_result is None:
            print(f"[Ошибка перевода] Не удалось сконвертировать {what_to_convert} в {what_to_convert_into}. Сервер курсов недоступен.")
            return False  # Метод вернет False, и GUI покажет ошибку вместо "Успех"

        # Если всё хорошо, безопасно распаковываем значения
        total_amount_after_convert = conversion_result[0]
        final_currency_name = conversion_result[1].upper()

        # 3. Выполнение перевода внутри Базы Данных (с автоматическим созданием кошелька получателю)
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Шаг А: Списываем деньги у отправителя (сумма + комиссия) в его валюте
                new_sender_balance = sender_balance - total_amount_to_deduct
                cursor.execute("""
                    UPDATE users_balances 
                    SET balance = ? 
                    WHERE account_id = ? AND currency = ?
                """, (new_sender_balance, sender_id, what_to_convert.upper()))
                
                # Шаг Б: Проверяем, есть ли у получателя кошелек в целевой валюте (final_currency_name)
                cursor.execute("""
                    SELECT balance FROM users_balances 
                    WHERE account_id = ? AND currency = ?
                """, (receiver_id, final_currency_name))
                receiver_row = cursor.fetchone()
                
                if receiver_row:
                    # Если кошелек существует, прибавляем к текущему балансу
                    new_receiver_balance = receiver_row[0] + total_amount_after_convert
                    cursor.execute("""
                        UPDATE users_balances 
                        SET balance = ? 
                        WHERE account_id = ? AND currency = ?
                    """, (new_receiver_balance, receiver_id, final_currency_name))
                else:
                    # НОВАЯ ЛОГИКА: Если кошелька нет, создаем его со стартовым балансом перевода!
                    cursor.execute("""
                        INSERT INTO users_balances (account_id, currency, balance)
                        VALUES (?, ?, ?)
                    """, (receiver_id, final_currency_name, total_amount_after_convert))
                    print(f"Для получателя автоматически создан новый кошелек в валюте {final_currency_name}")

                # Фиксация транзакции
                conn.commit()
                print(f"Перевод выполнен! Списано: {total_amount_to_deduct} {what_to_convert}. Зачислено: {total_amount_after_convert} {final_currency_name}")
                return comission
                
        except Exception as e:
            print(f"Ошибка базы данных при переводе: {e}")
            return False
    
    
    def create_account(self, owner_name, age):
        # Убрали balance из параметров
        return BankAccount(
            account_number=None,
            owner_name=owner_name,
            age=age,
            bank_name=self.bank_name
        )
    

    def find_account(self, account_number):
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM list_of_accounts WHERE account_number = ?", (account_number,))
            row = cursor.fetchone()
            if row:
                # Убрали initial_balance=0.0 отсюда
                return BankAccount(
                    account_number=row[0],
                    owner_name=row[1],
                    age=row[2],
                    bank_name=row[3]
                )
        return None
    

    def create_new_score_on_exists_account_with_new_currrency(self, owner_name, new_currency):
        db_path = get_db_path()
        search_name = owner_name.strip().title()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM list_of_accounts 
                    WHERE owner_name = ? AND bank_name = ?
                """, (search_name, self.bank_name))
                row = cursor.fetchone()
                
                if not row:
                    print(f"Ошибка: Пользователь '{search_name}' не найден в банке {self.bank_name}!")
                    return False
                
                account_id = row[0]
                
                cursor.execute("""
                    SELECT id FROM users_balances 
                    WHERE account_id = ? AND currency = ?
                """, (account_id, new_currency.upper()))
                
                if cursor.fetchone():
                    print(f"У аккаунта {search_name} в банке {self.bank_name} уже есть счет в валюте {new_currency.upper()}!")
                    return False
                
                cursor.execute("""
                    INSERT INTO users_balances (account_id, currency, balance)
                    VALUES (?, ?, ?)
                """, (account_id, new_currency.upper(), 0.0))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при создании валютного счета: {e}")
            return False


def setup_test_data():
    return [Bank("Privat Bank"), Bank("Monobank"), Bank("А-Bank"), Bank("Sense Bank")]


def convert_currency(what_to_convert, what_to_convert_into, quantity):
    if what_to_convert == what_to_convert_into:
        return [quantity, what_to_convert]
    else:
        return nbu_rate(what_to_convert, what_to_convert_into, quantity)


def nbu_rate(base, target, quantity):
    base = str(base).strip().upper()
    target = str(target).strip().upper()
    
    print(f"[Отладка курса] Пытаемся конвертировать: {base} -> {target}, количество: {quantity}")
    
    try:
        # Используем стабильный открытый API для получения курсов (эквивалент НБУ)
        url = "https://open.er-api.com/v6/latest/UAH"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        with requests.Session() as session:
            with session.get(url, headers=headers, timeout=5) as response:
                if response.status_code != 200:
                    print(f"[Отладка] Ошибка сервера курсов. Статус: {response.status_code}")
                    return None
                    
                data = response.json()
                
                # Этот API возвращает словарь с котировками относительно UAH в ключе 'rates'
                if "rates" not in data:
                    print("[Отладка] Неверная структура ответа API.")
                    return None
                
                rates = data["rates"]
                
                # Так как котировки идут относительно UAH (например, сколько USD в 1 грн),
                # мы переворачиваем их, чтобы получить чистый курс к гривне, как это было в НБУ:
                base_in_uah = 1.0 if base == "UAH" else (1.0 / float(rates[base]) if base in rates else None)
                target_in_uah = 1.0 if target == "UAH" else (1.0 / float(rates[target]) if target in rates else None)
                
                print(f"[Отладка] Курс {base} к UAH: {base_in_uah}")
                print(f"[Отладка] Курс {target} к UAH: {target_in_uah:.2f}")
                
                if base_in_uah is not None and target_in_uah is not None:
                    cross_rate = base_in_uah / target_in_uah
                    result = quantity * cross_rate
                    return [round(result, 2), target]
                else:
                    print(f"[Отладка] Валюта {base} или {target} не найдена.")
                    return None
                    
    except Exception as e:
        print(f"[Отладка] Ошибка сети или кода: {e}")
        return None