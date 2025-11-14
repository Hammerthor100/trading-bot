import requests
import time
import datetime

print("🤖 ТОРГОВЫЙ БОТ ЗАПУЩЕН!")
print("📊 Начинаю анализ...")

# ⚠️ ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА СВОИ!
TELEGRAM_TOKEN = "8537987175:AAHyuwgO_SJdrzL5pyjc11EfFjfHKrOC5-0"
CHAT_ID = "5819638872"

def get_crypto_price(symbol):
    """Получаем цену криптовалюты"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        return {
            'symbol': symbol,
            'price': float(data['lastPrice']),
            'change': float(data['priceChangePercent'])
        }
    except:
        return None

def send_telegram_message(message):
    """Отправляем сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

def analyze_market():
    """Анализируем рынок и отправляем сигнал"""
    # ⚠️ ВАЖНО: правильные символы!
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    for symbol in symbols:
        print(f"🔍 Проверяю {symbol}...")
        
        # Получаем данные
        data = get_crypto_price(symbol)
        
        if data:
            price = data['price']
            change = data['change']
            
            # Простой анализ
            if change > 1.5:
                signal = "🟢 ПОКУПАТЬ"
                reason = f"Цена выросла на {change:.2f}%"
            elif change < -1.5:
                signal = "🔴 ПРОДАВАТЬ" 
                reason = f"Цена упала на {abs(change):.2f}%"
            else:
                signal = "🟡 ЖДАТЬ"
                reason = f"Изменение {change:.2f}% - нет четкого сигнала"
            
            # Если есть сигнал - отправляем
            if signal != "🟡 ЖДАТЬ":
                # Формируем сообщение
                message = f"""
🎯 <b>ТОРГОВЫЙ СИГНАЛ</b>

💰 <b>Пара:</b> {symbol}
📊 <b>Сигнал:</b> {signal}
💵 <b>Цена:</b> ${price:.2f}
📈 <b>Изменение:</b> {change:.2f}%

📋 <b>Причина:</b> {reason}

⏰ <b>Время:</b> {datetime.datetime.now().strftime('%H:%M:%S')}

⚠️ <i>Это тестовый сигнал!</i>
                """
                
                # Отправляем в Telegram
                if send_telegram_message(message):
                    print(f"✅ Сигнал {signal} для {symbol}!")
                    print(f"✅ Отправлено в Telegram!")
                else:
                    print(f"❌ Ошибка отправки для {symbol}")
            else:
                print(f"➖ Нет сигнала")
        else:
            print(f"❌ Не удалось получить данные для {symbol}")
        
        # Ждем 2 секунды между запросами
        time.sleep(2)

# Запускаем анализ
analyze_market()
print("🎉 Анализ завершен!")
