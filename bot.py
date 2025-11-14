import requests
import matplotlib.pyplot as plt
import datetime
import time
import os

class TradingBot:
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        # ⚠️ ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ!
        self.telegram_token = "8537987175:AAEXsTlBnv-f5troBotT_VdLuFs8F1cQFrk"
        self.chat_id = "5819638872"
        
    def get_price(self, symbol):
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(url)
            data = response.json()
            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
                'change': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice'])
            }
        except Exception as e:
            print(f"Ошибка: {e}")
            return None
    
    def analyze(self, price_data):
        if not price_data:
            return "HOLD", 0, ["Ошибка данных"]
            
        signals = []
        reasons = []
        
        if price_data['change'] > 2:
            signals.append('BUY')
            reasons.append(f"📈 Цена +{price_data['change']:.2f}%")
        elif price_data['change'] < -2:
            signals.append('SELL') 
            reasons.append(f"📉 Цена {price_data['change']:.2f}%")
            
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            return 'BUY', 70, reasons
        elif sell_count > buy_count:
            return 'SELL', 70, reasons
        else:
            return 'HOLD', 0, ["Нет сигналов"]
    
    def create_chart(self, symbol, price_data, signal, confidence, reasons):
        plt.figure(figsize=(10, 6))
        plt.style.use('dark_background')
        
        prices = [price_data['low'], price_data['price'], price_data['high']]
        labels = ['Min', 'Current', 'Max']
        colors = ['red', 'yellow', 'green']
        
        plt.bar(labels, prices, color=colors, alpha=0.7)
        plt.title(f'Сигнал: {symbol} - {signal}', fontsize=16, color='white')
        plt.ylabel('Цена ($)')
        
        info_text = f"Цена: ${price_data['price']:.2f}\nИзменение: {price_data['change']:.2f}%"
        plt.figtext(0.15, 0.02, info_text, fontsize=10, color='lightblue')
        
        if not os.path.exists('charts'):
            os.makedirs('charts')
            
        filename = f"charts/signal_{symbol}.png"
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def send_telegram_message(self, message, image_path=None):
        try:
            if image_path and os.path.exists(image_path):
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendPhoto"
                with open(image_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': self.chat_id, 'caption': message}
                    response = requests.post(url, files=files, data=data)
            else:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                data = {'chat_id': self.chat_id, 'text': message}
                response = requests.post(url, data=data)
            
            return True
        except Exception as e:
            print(f"Ошибка Telegram: {e}")
            return False
    
    def run_once(self):
        print("🚀 Запускаю анализ...")
        
        for symbol in self.symbols:
            print(f"🔍 Проверяю {symbol}...")
            
            price_data = self.get_price(symbol)
            
            if price_data:
                signal, confidence, reasons = self.analyze(price_data)
                
                if signal != 'HOLD':
                    print(f"🎯 Сигнал {signal} для {symbol}!")
                    
                    # Создаем график
                    chart_path = self.create_chart(symbol, price_data, signal, confidence, reasons)
                    
                    # Формируем сообщение
                    message = f"""
🎯 СИГНАЛ: {signal}
💰 Пара: {symbol}
💵 Цена: ${price_data['price']:.2f}
📊 Изменение: {price_data['change']:.2f}%

📋 Причины:
{chr(10).join(reasons)}

⏰ Время: {datetime.datetime.now().strftime('%H:%M')}
                    """
                    
                    # Отправляем в Telegram
                    if self.send_telegram_message(message, chart_path):
                        print(f"✅ Отправлено в Telegram!")
                    else:
                        print(f"❌ Ошибка отправки")
                else:
                    print(f"➖ Нет сигнала")
            
            time.sleep(1)

# Запуск
if __name__ == "__main__":
    bot = TradingBot()
    bot.run_once()
