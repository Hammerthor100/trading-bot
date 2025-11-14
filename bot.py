import requests
import time
import datetime
import json
import matplotlib.pyplot as plt
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

print("🎮 ТРЕЙДИНГ БОТ С КРАСИВЫМИ КНОПКАМИ ЗАГРУЖАЕТСЯ...")

# ⚠️ ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ!
TELEGRAM_TOKEN = "8537987175:AAHyuwgO_SJdrzL5pyjc11EfFjfHKrOC5-0"
CHAT_ID = "5819638872"

class CreativeTradingBot:
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        self.signals_history = []
        
    def create_main_keyboard(self):
        """Создаем главное меню с красивыми кнопками"""
        keyboard = [
            ["🚀 Сделать анализ", "📈 Статус бота"],
            ["💎 Топ сигналы", "🎯 Быстрый анализ"],
            ["📊 Графики", "🆘 Помощь"],
            ["⚡ Экспресс анализ", "❤️ Избранные пары"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие...")

    def create_analysis_keyboard(self):
        """Клавиатура для анализа"""
        keyboard = [
            ["🔍 Полный анализ", "🎯 Сигналы BTC"],
            ["📊 Сигналы ETH", "💎 Сигналы ADA"],
            ["↩️ Назад в меню"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    def get_crypto_data(self, symbol):
        """Получаем расширенные данные"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(url)
            data = response.json()
            
            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
                'change': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
        except Exception as e:
            print(f"Ошибка получения данных {symbol}: {e}")
            return None

    def analyze_symbol(self, symbol_data):
        """Анализ символа"""
        if not symbol_data:
            return "HOLD", 0, ["Ошибка данных"], {}
            
        price = symbol_data['price']
        change = symbol_data['change']
        volume = symbol_data['volume']
        
        signals = []
        reasons = []
        indicators = {
            'price': price,
            'change': change,
            'volume': volume
        }
        
        # Анализ цены
        if change > 3:
            signals.append('BUY')
            reasons.append(f"🚀 Цена взлетела на {change:.2f}%")
        elif change > 1:
            signals.append('BUY')
            reasons.append(f"📈 Цена растет +{change:.2f}%")
        elif change < -3:
            signals.append('SELL')
            reasons.append(f"🔻 Цена рухнула на {abs(change):.2f}%")
        elif change < -1:
            signals.append('SELL')
            reasons.append(f"📉 Цена падает {change:.2f}%")
        
        # Анализ объема
        if volume > 50000:
            reasons.append(f"💎 Высокий объем: {volume:.0f} BTC")
        
        # Случайный RSI для демо
        rsi = 40 + (change * 2)
        indicators['rsi'] = round(rsi, 1)
        
        if rsi < 30:
            signals.append('BUY')
            reasons.append(f"🎯 RSI {rsi:.1f} - СИЛЬНАЯ ПЕРЕПРОДАННОСТЬ")
        elif rsi > 70:
            signals.append('SELL')
            reasons.append(f"🎯 RSI {rsi:.1f} - СИЛЬНАЯ ПЕРЕКУПЛЕННОСТЬ")
        
        # Определяем итоговый сигнал
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            confidence = min(95, buy_count * 25 + 30)
            final_signal = '🟢 ПОКУПАТЬ'
        elif sell_count > buy_count:
            confidence = min(95, sell_count * 25 + 30)
            final_signal = '🔴 ПРОДАВАТЬ'
        else:
            confidence = 0
            final_signal = '🟡 ЖДАТЬ'
            reasons.append("⚖️ Сигналы противоречивы")
        
        return final_signal, confidence, reasons, indicators

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start - главное меню"""
        welcome_text = """
🎮 *ДОБРО ПОЖАЛОВАТЬ В ТРЕЙДИНГ БОТ* 🎮

✨ *Что я умею:*
• 🚀 Анализировать крипторынок в реальном времени
• 📈 Показывать сигналы покупки/продажи
• 💎 Создавать красивые графики
• 🎯 Давать рекомендации с уверенностью

🎯 *Выберите действие снизу:* 👇
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений (нажатия кнопок)"""
        text = update.message.text
        
        if text == "🚀 Сделать анализ":
            await self.full_analysis(update)
        elif text == "📈 Статус бота":
            await self.show_status(update)
        elif text == "💎 Топ сигналы":
            await self.top_signals(update)
        elif text == "🎯 Быстрый анализ":
            await self.quick_analysis(update)
        elif text == "📊 Графики":
            await self.show_charts_menu(update)
        elif text == "🆘 Помощь":
            await self.show_help(update)
        elif text == "⚡ Экспресс анализ":
            await self.express_analysis(update)
        elif text == "❤️ Избранные пары":
            await self.favorite_pairs(update)
        elif text == "↩️ Назад в меню":
            await self.back_to_menu(update)
        elif text == "🔍 Полный анализ":
            await self.full_analysis(update)
        elif text == "🎯 Сигналы BTC":
            await self.analyze_btc(update)
        elif text == "📊 Сигналы ETH":
            await self.analyze_eth(update)
        elif text == "💎 Сигналы ADA":
            await self.analyze_ada(update)

    async def full_analysis(self, update: Update):
        """Полный анализ всех пар"""
        message = await update.message.reply_text("🔮 *Запускаю магию анализа...*", parse_mode='Markdown')
        
        analysis_results = []
        
        for symbol in self.symbols:
            try:
                data = self.get_crypto_data(symbol)
                if data:
                    signal, confidence, reasons, indicators = self.analyze_symbol(data)
                    
                    if signal != '🟡 ЖДАТЬ':
                        emoji = "🟢" if "ПОКУПАТЬ" in signal else "🔴"
                        analysis_results.append(
                            f"{emoji} *{symbol}*: {signal}\n"
                            f"   💰 ${data['price']:.2f} | 📈 {data['change']:.2f}% | 💪 {confidence}%\n"
                            f"   🎯 {reasons[0] if reasons else 'Нет сигналов'}"
                        )
                        
                        # Сохраняем в историю
                        self.signals_history.append({
                            'symbol': symbol,
                            'signal': signal,
                            'confidence': confidence,
                            'timestamp': datetime.datetime.now().isoformat()
                        })
                
                time.sleep(0.5)  # Пауза между запросами
                
            except Exception as e:
                print(f"Ошибка анализа {symbol}: {e}")
        
        if analysis_results:
            result_text = "🎊 *РЕЗУЛЬТАТЫ АНАЛИЗА:*\n\n" + "\n\n".join(analysis_results)
        else:
            result_text = "🤷 *Сигналов не найдено*\nПопробуйте позже!"
        
        await message.edit_text(result_text, parse_mode='Markdown')

    async def quick_analysis(self, update: Update):
        """Быстрый анализ"""
        await update.message.reply_text(
            "⚡ *Быстрый анализ запущен!*\n"
            "Проверяю основные пары...",
            parse_mode='Markdown'
        )
        
        # Анализируем только BTC и ETH
        quick_pairs = ['BTCUSDT', 'ETHUSDT']
        results = []
        
        for symbol in quick_pairs:
            data = self.get_crypto_data(symbol)
            if data:
                signal, confidence, reasons, indicators = self.analyze_symbol(data)
                arrow = "↗️" if data['change'] > 0 else "↘️"
                results.append(
                    f"{arrow} *{symbol}*: ${data['price']:.2f} ({data['change']:.2f}%)\n"
                    f"   Сигнал: {signal} | Уверенность: {confidence}%"
                )
        
        result_text = "🎯 *БЫСТРЫЙ АНАЛИЗ:*\n\n" + "\n\n".join(results)
        await update.message.reply_text(result_text, parse_mode='Markdown')

    async def top_signals(self, update: Update):
        """Топ сигналы"""
        if not self.signals_history:
            await update.message.reply_text("📭 *История сигналов пуста*\nСначала сделайте анализ!")
            return
        
        # Берем последние 5 сигналов
        recent_signals = self.signals_history[-5:]
        
        signals_text = "🏆 *ПОСЛЕДНИЕ СИГНАЛЫ:*\n\n"
        
        for signal in reversed(recent_signals):
            time_ago = datetime.datetime.now() - datetime.datetime.fromisoformat(signal['timestamp'])
            minutes_ago = int(time_ago.total_seconds() / 60)
            
            signals_text += (
                f"💎 *{signal['symbol']}*: {signal['signal']}\n"
                f"   🔥 Уверенность: {signal['confidence']}%\n"
                f"   ⏰ {minutes_ago} мин. назад\n\n"
            )
        
        await update.message.reply_text(signals_text, parse_mode='Markdown')

    async def show_status(self, update: Update):
        """Статус бота"""
        status_text = (
            "📊 *СТАТУС БОТА*\n\n"
            f"✅ *Бот активен:* {datetime.datetime.now().strftime('%H:%M:%S')}\n"
            f"🔍 *Мониторю пар:* {len(self.symbols)}\n"
            f"📈 *Всего сигналов:* {len(self.signals_history)}\n"
            f"🎯 *Последний анализ:* {len(self.signals_history) and datetime.datetime.fromisoformat(self.signals_history[-1]['timestamp']).strftime('%H:%M') or 'Нет'}\n\n"
            "💡 *Статистика за сегодня:*\n"
            f"   🟢 Покупка: {len([s for s in self.signals_history if 'ПОКУПАТЬ' in s['signal']])}\n"
            f"   🔴 Продажа: {len([s for s in self.signals_history if 'ПРОДАВАТЬ' in s['signal']])}\n"
            f"   🟡 Ожидание: {len([s for s in self.signals_history if 'ЖДАТЬ' in s['signal']])}"
        )
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def show_help(self, update: Update):
        """Помощь"""
        help_text = """
🆘 *ПОМОЩЬ ПО БОТУ* 🆘

🎮 *Кнопки меню:*
🚀 *Сделать анализ* - Полная проверка всех пар
📈 *Статус бота* - Статистика и история
💎 *Топ сигналы* - Последние рекомендации
🎯 *Быстрый анализ* - Только BTC и ETH
📊 *Графики* - Визуализация анализа
⚡ *Экспресс анализ* - Ультра-быстрая проверка
❤️ *Избранные пары* - Ваши любимые пары

🎯 *Сигналы:*
🟢 ПОКУПАТЬ - Сильные бычьи сигналы
🔴 ПРОДАВАТЬ - Сильные медвежьи сигналы  
🟡 ЖДАТЬ - Нет четких сигналов

⚠️ *Важно:* Это обучающий бот!
Не используйте для реальной торговли!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def express_analysis(self, update: Update):
        """Экспресс анализ"""
        await update.message.reply_text(
            "⚡ *ЭКСПРЕСС-АНАЛИЗ!*\n"
            "Мгновенная проверка рынка...",
            parse_mode='Markdown'
        )
        
        # Только BTC быстрая проверка
        data = self.get_crypto_data('BTCUSDT')
        if data:
            change = data['change']
            if change > 2:
                signal = "🚀 СИЛЬНЫЙ РОСТ!"
            elif change > 0:
                signal = "📈 Растет"
            elif change < -2:
                signal = "🔻 СИЛЬНОЕ ПАДЕНИЕ!"
            else:
                signal = "➡️ Боковик"
            
            result = (
                f"🎯 *BITCOIN (BTC)*\n"
                f"💰 Цена: ${data['price']:.2f}\n"
                f"📊 Изменение: {change:.2f}%\n"
                f"🏆 Статус: {signal}\n\n"
                f"💡 *Рекомендация:* {'Покупать' if change > 1 else 'Продавать' if change < -1 else 'Ждать'}"
            )
        else:
            result = "❌ *Ошибка получения данных*"
        
        await update.message.reply_text(result, parse_mode='Markdown')

    async def favorite_pairs(self, update: Update):
        """Избранные пары"""
        favorites_text = (
            "❤️ *ИЗБРАННЫЕ ПАРЫ*\n\n"
            "💎 *BTC/USDT* - Биткоин\n"
            "🔵 *ETH/USDT* - Эфириум\n"
            "🟣 *ADA/USDT* - Кардано\n"
            "🟠 *DOT/USDT* - Полкадот\n"
            "🔗 *LINK/USDT* - Чейнлинк\n\n"
            "🎯 *Для анализа выберите:*\n"
            "🚀 Сделать анализ - все пары\n"
            "🎯 Быстрый анализ - BTC/ETH"
        )
        await update.message.reply_text(favorites_text, parse_mode='Markdown')

    async def analyze_btc(self, update: Update):
        """Анализ только BTC"""
        await self.analyze_single_pair(update, 'BTCUSDT', 'BITCOIN')

    async def analyze_eth(self, update: Update):
        """Анализ только ETH"""
        await self.analyze_single_pair(update, 'ETHUSDT', 'ETHEREUM')

    async def analyze_ada(self, update: Update):
        """Анализ только ADA"""
        await self.analyze_single_pair(update, 'ADAUSDT', 'CARDANO')

    async def analyze_single_pair(self, update: Update, symbol, name):
        """Анализ одной пары"""
        data = self.get_crypto_data(symbol)
        if data:
            signal, confidence, reasons, indicators = self.analyze_symbol(data)
            
            result_text = (
                f"🎯 *ДЕТАЛЬНЫЙ АНАЛИЗ {name}*\n\n"
                f"💰 *Цена:* ${data['price']:.2f}\n"
                f"📈 *Изменение:* {data['change']:.2f}%\n"
                f"🎯 *Сигнал:* {signal}\n"
                f"💪 *Уверенность:* {confidence}%\n"
                f"📊 *RSI:* {indicators.get('rsi', 'N/A')}\n\n"
                f"📋 *Обоснование:*\n"
            )
            
            for reason in reasons[:2]:
                result_text += f"   • {reason}\n"
                
        else:
            result_text = f"❌ *Ошибка анализа {name}*"
        
        await update.message.reply_text(result_text, parse_mode='Markdown')

    async def show_charts_menu(self, update: Update):
        """Меню графиков"""
        await update.message.reply_text(
            "📊 *РАЗДЕЛ ГРАФИКОВ*\n\n"
            "Выберите тип анализа:",
            reply_markup=self.create_analysis_keyboard(),
            parse_mode='Markdown'
        )

    async def back_to_menu(self, update: Update):
        """Назад в главное меню"""
        await update.message.reply_text(
            "↩️ *Возвращаюсь в главное меню*",
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

# Создаем и запускаем бота
bot = CreativeTradingBot()

def main():
    """Запускаем бота"""
    print("🎮 Создаю Telegram бота с красивыми кнопками...")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("✅ Бот запущен! Ожидаю команды...")
    print("📱 Перейдите в Telegram и напишите /start")
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
