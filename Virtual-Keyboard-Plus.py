import tkinter as tk
from tkinter import filedialog, messagebox
import pyperclip

class VirtualKeyboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Keyboard Plus")
        
        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Устанавливаем размер окна: половина ширины экрана и полная высота минус панель задач
        window_width = screen_width // 2
        window_height = screen_height - 60
        
        # Позиционируем окно слева (x=0, y=0)
        self.root.geometry(f"{window_width}x{window_height}+0+0")
        self.root.configure(bg="#1a1a2e")
        
        # Раскладки клавиатур
        self.layouts = {
            'EN': [
                ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
                ['Tab', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
                ['Caps', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'Enter'],
                ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'Shift'],
                ['Ctrl', 'Alt', 'Space', 'Alt', 'Ctrl']
            ],
            'RU': [
                ['ё', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
                ['Tab', 'й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ', '\\'],
                ['Caps', 'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э', 'Enter'],
                ['Shift', 'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', '.', 'Shift'],
                ['Ctrl', 'Alt', 'Space', 'Alt', 'Ctrl']
            ],
            'UA': [
                ["'", '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
                ['Tab', 'й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ї', '\\'],
                ['Caps', 'ф', 'і', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'є', 'Enter'],
                ['Shift', 'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', '.', 'Shift'],
                ['Ctrl', 'Alt', 'Space', 'Alt', 'Ctrl']
            ]
        }
        
        # Shift-модификаторы для разных языков
        self.shift_maps = {
            'EN': {
                '`': '~', '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
                ';': ':', "'": '"', ',': '<', '.': '>', '/': '?'
            },
            'RU': {
                '1': '!', '2': '"', '3': '№', '4': ';', '5': '%',
                '6': ':', '7': '?', '8': '*', '9': '(', '0': ')',
                '-': '_', '=': '+', '.': ',', 'ё': 'Ё'
            },
            'UA': {
                '1': '!', '2': '"', '3': '№', '4': ';', '5': '%',
                '6': ':', '7': '?', '8': '*', '9': '(', '0': ')',
                '-': '_', '=': '+', '.': ',', "'": '₴'
            }
        }
        
        self.current_layout = 'RU'
        self.caps_lock = False
        self.shift_pressed = False
        self.is_modified = False
        self.current_file = None
        self.key_buttons = {}
        self.lang_buttons = {}
        
        # Оптимизированная система undo/redo
        self.undo_stack = []
        self.redo_stack = []
        self.last_saved_text = "\n"
        self.undo_in_progress = False
        
        # УЛУЧШЕННАЯ система сохранения состояний
        self.save_timer = None
        self.pending_save = False
        self.last_input_time = 0
        
        # ⚙️ НАСТРОЙКА UNDO: Время паузы для группировки символов
        # Если между нажатиями клавиш проходит МЕНЬШЕ этого времени - символы группируются
        # Если БОЛЬШЕ - создаётся новое состояние для undo
        # 
        # Примеры:
        # 300 мс (0.3 сек) - очень быстрый набор, удаляет по несколько букв
        # 500 мс (0.5 сек) - средний набор, удаляет небольшие группы букв  
        # 1000 мс (1 сек) - медленный набор, удаляет по 1-2 буквы
        # 1500 мс (1.5 сек) - очень медленный, почти каждая буква отдельно
        self.typing_pause_threshold = 300  # ⬅️ ИЗМЕНИТЕ ЭТО ЗНАЧЕНИЕ
        
        # УЛУЧШЕННАЯ система сохранения состояний
        self.save_timer = None
        self.pending_save = False
        self.last_input_time = 0
        self.typing_pause_threshold = 10  # 1 секунда паузы = новое состояние
        
        # ОПТИМИЗАЦИЯ: Кэш для цветов кнопок
        self.color_cache = {
            'special_normal': "#533483",
            'special_active': "#6b46a6",
            'regular_normal': "#16213e",
            'regular_active': "#0f3460",
            'caps_active': "#e94560",
            'shift_active': "#e94560",
            'lang_active': "#10b981",
            'lang_inactive': "#e94560"
        }
        
        self.create_ui()
        
        # ИСПРАВЛЕНИЕ: Привязка событий физической клавиатуры
        self.text_area.bind('<Key>', self.on_physical_key_press)
        # Привязка по keycode - работает на ВСЕХ раскладках
        self.text_area.bind('<Control-Key>', self.on_ctrl_key_universal)
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        # Главный фрейм
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Текстовое поле
        text_frame = tk.Frame(main_frame, bg="#16213e", bd=2, relief=tk.RAISED)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_area = tk.Text(
            text_frame, font=("Arial", 14),
            bg="#0f3460", fg="#e94560",
            insertbackground="#e94560",
            wrap=tk.WORD, undo=False,
            yscrollcommand=scrollbar.set
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)
        
        # Отслеживание изменений
        self.text_area.bind("<<Modified>>", self.on_text_modified)
        
        # Контекстное меню (правая кнопка мыши)
        self.create_context_menu()
        
        # Панель управления
        control_frame = tk.Frame(main_frame, bg="#1a1a2e")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        buttons_frame = tk.Frame(control_frame, bg="#1a1a2e")
        buttons_frame.pack(anchor=tk.CENTER)
        
        # ОПТИМИЗАЦИЯ: Конфигурация кнопок в списке для упрощения создания
        button_configs = [
            ("↶ Назад", self.undo, "#f59e0b", "#fbbf24"),
            ("↷ Вперёд", self.redo, "#f59e0b", "#fbbf24"),
            ("◌́ Ударение", self.add_accent, "#00d2d3", "#01e4e5"),
            ("📋 Копировать", self.smart_copy, "#8b5cf6", "#a78bfa"),
            ("📄 Вставить", self.paste_text, "#8b5cf6", "#a78bfa"),
            ("🗑 Очистить", self.clear_text, "#ef4444", "#f87171"),
            ("📂 Открыть", self.open_file, "#3b82f6", "#60a5fa"),
            ("💾 Сохранить", self.save_file, "#10b981", "#34d399")
        ]
        
        for text, command, bg, active_bg in button_configs:
            btn = tk.Button(buttons_frame, text=text, command=command,
                          font=("Arial", 10, "bold"), bg=bg, fg="white",
                          activebackground=active_bg, relief=tk.FLAT, 
                          padx=15, pady=5, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2)
        
        # Фрейм клавиатуры
        self.keyboard_frame = tk.Frame(main_frame, bg="#1a1a2e")
        self.keyboard_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))
        
        self.create_keyboard()
        
    def create_keyboard(self):
        # ОПТИМИЗАЦИЯ: Очищаем только если нужно полное пересоздание
        for widget in self.keyboard_frame.winfo_children():
            widget.destroy()
        
        self.key_buttons = {}
        self.caps_button = None
        self.shift_buttons = []
        layout = self.layouts[self.current_layout]
        
        for row in layout:
            row_frame = tk.Frame(self.keyboard_frame, bg="#1a1a2e")
            row_frame.pack(pady=2)
            
            for key in row:
                width = 30 if key == 'Space' else (8 if key in ['Backspace', 'Tab', 'Enter', 'Shift', 'Caps'] else 4)
                
                # ОПТИМИЗАЦИЯ: Используем кэш цветов
                is_special = key in ['Backspace', 'Tab', 'Enter', 'Shift', 'Caps', 'Ctrl', 'Alt']
                bg_color = self.color_cache['special_normal'] if is_special else self.color_cache['regular_normal']
                active_bg = self.color_cache['special_active'] if is_special else self.color_cache['regular_active']
                
                display_text = self.get_display_text(key)
                
                btn = tk.Button(
                    row_frame, text=display_text, width=width, height=2,
                    font=("Arial", 11, "bold"), bg=bg_color, fg="white",
                    activebackground=active_bg, activeforeground="white",
                    relief=tk.FLAT, bd=0, command=lambda k=key: self.key_press(k),
                    cursor="hand2"
                )
                btn.pack(side=tk.LEFT, padx=2)
                
                if key == 'Caps':
                    self.caps_button = btn
                elif key == 'Shift':
                    self.shift_buttons.append(btn)
                elif len(key) == 1:
                    self.key_buttons[key] = btn
        
        # Кнопки выбора языка
        lang_row_frame = tk.Frame(self.keyboard_frame, bg="#1a1a2e")
        lang_row_frame.pack(pady=(10, 2))
        
        for lang in ['EN', 'RU', 'UA']:
            lang_btn = tk.Button(
                lang_row_frame, text=lang,
                command=lambda l=lang: self.change_layout(l),
                font=("Arial", 11, "bold"), fg="white",
                activebackground="#ff6b81", relief=tk.FLAT,
                width=8, height=2, bd=0, cursor="hand2"
            )
            lang_btn.pack(side=tk.LEFT, padx=3)
            self.lang_buttons[lang] = lang_btn
        
        self.update_lang_buttons()
    
    def create_context_menu(self):
        """Создаёт контекстное меню для текстового поля"""
        self.context_menu = tk.Menu(self.root, tearoff=0, 
                                     bg="#16213e", fg="white",
                                     activebackground="#0f3460", 
                                     activeforeground="white",
                                     font=("Arial", 10))
        
        self.context_menu.add_command(label="✂ Вырезать", command=self.cut_text)
        self.context_menu.add_command(label="📋 Копировать", command=self.copy_selected_text)
        self.context_menu.add_command(label="📄 Вставить", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔍 Выделить всё", command=self.select_all_text)
        
        # Привязываем контекстное меню к правой кнопке мыши
        self.text_area.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Показывает контекстное меню в месте клика"""
        try:
            # Проверяем есть ли выделение
            has_selection = self.text_area.tag_ranges(tk.SEL)
            
            # Активируем/деактивируем пункты в зависимости от наличия выделения
            if has_selection:
                self.context_menu.entryconfig("✂ Вырезать", state=tk.NORMAL)
                self.context_menu.entryconfig("📋 Копировать", state=tk.NORMAL)
            else:
                self.context_menu.entryconfig("✂ Вырезать", state=tk.DISABLED)
                self.context_menu.entryconfig("📋 Копировать", state=tk.DISABLED)
            
            # Показываем меню
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def save_undo_state(self, force=False):
        """УЛУЧШЕНО: Умное сохранение - после пробелов/Enter или паузы в наборе"""
        if self.undo_in_progress:
            return
        
        import time
        current_time = int(time.time() * 1000)  # в миллисекундах
        time_since_last = current_time - self.last_input_time
        
        # Сохраняем сразу если:
        # 1. force=True (принудительно)
        # 2. Прошла пауза в наборе (>1 сек)
        # 3. Это первый ввод
        if force or time_since_last > self.typing_pause_threshold or self.last_input_time == 0:
            self.last_input_time = current_time
            self._do_save_undo_state()
        else:
            # Иначе откладываем сохранение
            self.last_input_time = current_time
            if self.save_timer:
                self.root.after_cancel(self.save_timer)
            self.save_timer = self.root.after(self.typing_pause_threshold, self._do_save_undo_state)
            self.pending_save = True
    
    def _do_save_undo_state(self):
        """Реально сохраняет состояние"""
        if self.undo_in_progress:
            return
        
        self.pending_save = False
        
        try:
            current_text = self.text_area.get("1.0", tk.END)
        except:
            return
        
        # Сохраняем только если текст изменился
        if current_text != self.last_saved_text:
            self.undo_stack.append(self.last_saved_text)
            self.last_saved_text = current_text
            self.redo_stack.clear()
            
            # Ограничиваем размер стека (максимум 500 операций для экономии памяти)
            if len(self.undo_stack) > 500:
                self.undo_stack.pop(0)
    
    def get_display_text(self, key):
        """Определяет текст для отображения на клавише"""
        if key in ['Backspace', 'Tab', 'Enter', 'Shift', 'Caps', 'Ctrl', 'Alt', 'Space']:
            return key
        
        # Если Shift нажат и есть специальный символ
        if self.shift_pressed and key in self.shift_maps[self.current_layout]:
            return self.shift_maps[self.current_layout][key]
        
        # Если Caps Lock или Shift - показываем заглавную букву
        if (self.caps_lock or self.shift_pressed) and len(key) == 1 and key.isalpha():
            return key.upper()
        
        return key
    
    def key_press(self, key):
        if key == 'Backspace':
            try:
                pos = self.text_area.index(tk.INSERT)
                if pos != "1.0":
                    self.text_area.delete(f"{pos}-1c", pos)
                    self.save_undo_state(force=True)  # Принудительно после удаления
            except tk.TclError:
                pass
        elif key == 'Enter':
            self.text_area.insert(tk.INSERT, '\n')
            self.save_undo_state(force=True)  # Принудительно после Enter
        elif key == 'Space':
            self.text_area.insert(tk.INSERT, ' ')
            self.save_undo_state(force=True)  # Принудительно после пробела
        elif key == 'Tab':
            self.text_area.insert(tk.INSERT, '    ')
            self.save_undo_state(force=True)
        elif key == 'Caps':
            self.caps_lock = not self.caps_lock
            self.update_key_display()
        elif key == 'Shift':
            self.shift_pressed = not self.shift_pressed
            self.update_key_display()
        elif key in ['Ctrl', 'Alt']:
            pass
        else:
            char = key
            if self.shift_pressed and key in self.shift_maps[self.current_layout]:
                char = self.shift_maps[self.current_layout][key]
                self.shift_pressed = False
                self.update_key_display()
            elif (self.shift_pressed or self.caps_lock) and len(key) == 1 and key.isalpha():
                char = char.upper()
                if self.shift_pressed:
                    self.shift_pressed = False
                    self.update_key_display()
            
            self.text_area.insert(tk.INSERT, char)
            self.save_undo_state()  # Обычное сохранение для букв
    
    def update_key_display(self):
        """ОПТИМИЗАЦИЯ: Обновляем только изменившиеся кнопки"""
        # Обновляем текст на буквенных клавишах
        for key, button in self.key_buttons.items():
            new_text = self.get_display_text(key)
            if button['text'] != new_text:
                button.config(text=new_text)
        
        # Обновляем Caps Lock
        if self.caps_button:
            new_bg = self.color_cache['caps_active'] if self.caps_lock else self.color_cache['special_normal']
            if self.caps_button['bg'] != new_bg:
                self.caps_button.config(bg=new_bg)
        
        # Обновляем Shift
        new_shift_bg = self.color_cache['shift_active'] if self.shift_pressed else self.color_cache['special_normal']
        for shift_btn in self.shift_buttons:
            if shift_btn['bg'] != new_shift_bg:
                shift_btn.config(bg=new_shift_bg)
    
    def update_lang_buttons(self):
        """ОПТИМИЗАЦИЯ: Обновляем только изменившиеся кнопки языков"""
        for lang, button in self.lang_buttons.items():
            new_bg = self.color_cache['lang_active'] if lang == self.current_layout else self.color_cache['lang_inactive']
            if button['bg'] != new_bg:
                button.config(bg=new_bg)
    
    def change_layout(self, lang):
        """ОПТИМИЗАЦИЯ: Не пересоздаем клавиатуру, если язык не изменился"""
        if self.current_layout == lang:
            return
        
        self.current_layout = lang
        self.create_keyboard()
        self.update_key_display()
    
    def on_physical_key_press(self, event):
        """Обработка ввода с физической клавиатуры"""
        # Список служебных клавиш
        non_printable = {
            'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 
            'Shift_L', 'Shift_R', 'Caps_Lock', 'Super_L', 'Super_R',
            'Win_L', 'Win_R', 'Menu', 'Num_Lock', 'Scroll_Lock',
            'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next',
            'Insert', 'Pause', 'Print', 'F1', 'F2', 'F3', 'F4',
            'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'
        }
        
        # Игнорируем служебные клавиши
        if event.keysym in non_printable:
            return None
        
        # Игнорируем комбинации с Ctrl (они обрабатываются отдельно)
        if event.state & 0x4:
            return None
        
        # Определяем тип символа для умного сохранения
        char = event.char
        
        # Сохраняем принудительно после:
        # - Enter
        # - Пробел
        # - Backspace/Delete
        if event.keysym in ['Return', 'space', 'BackSpace', 'Delete']:
            self.root.after_idle(lambda: self.save_undo_state(force=True))
        else:
            # Для обычных символов - умное сохранение
            self.root.after_idle(self.save_undo_state)
        
        return None
    
    def on_ctrl_key_universal(self, event):
        """ИСПРАВЛЕНО: Универсальная обработка Ctrl+клавиша (работает на ВСЕХ раскладках!)"""
        # Используем keycode вместо keysym - keycode не зависит от раскладки!
        # Linux keycodes: Z=52, Y=29, V=55, C=54, X=53, A=38
        # Windows/Mac keycodes: Z=90, Y=89, V=86, C=67, X=88, A=65
        # Также проверяем keysym для надежности
        
        keysym_lower = event.keysym.lower()
        keycode = event.keycode
        
        # Проверяем Z (русская Я, украинская Я)
        is_z_key = (keycode in [52, 90] or keysym_lower in ['z', 'я'])
        
        # Проверяем Y (русская Н, украинская Н)  
        is_y_key = (keycode in [29, 89] or keysym_lower in ['y', 'н', 'n'])
        
        # Проверяем V (русская М, украинская М)
        is_v_key = (keycode in [55, 86] or keysym_lower in ['v', 'м', 'm'])
        
        # Проверяем C (русская С, украинская С)
        is_c_key = (keycode in [54, 67] or keysym_lower in ['c', 'с'])
        
        # Проверяем X (русская Ч, украинская Ч)
        is_x_key = (keycode in [53, 88] or keysym_lower in ['x', 'ч'])
        
        # Проверяем A (русская Ф, украинская Ф)
        is_a_key = (keycode in [38, 65] or keysym_lower in ['a', 'ф'])
        
        if is_z_key:
            # Ctrl+Shift+Z = Redo
            if event.state & 0x1:  # Shift нажат
                self.redo()
                return "break"
            # Ctrl+Z = Undo
            else:
                self.undo()
                return "break"
        
        elif is_y_key:
            # Ctrl+Y = Redo
            self.redo()
            return "break"
        
        elif is_v_key:
            # Ctrl+V = Paste
            self.paste_text()
            return "break"
        
        elif is_c_key:
            # Ctrl+C = Smart Copy (выделенное или всё)
            self.smart_copy()
            return "break"
        
        elif is_x_key:
            # Ctrl+X = Cut
            self.cut_text()
            return "break"
        
        elif is_a_key:
            # Ctrl+A = Select All
            self.select_all_text()
            return "break"
        
        # Для остальных комбинаций - пропускаем стандартную обработку
        return None
    
    def undo(self):
        """Отменить последнее действие"""
        # Сохраняем pending изменение перед undo
        if self.pending_save:
            if self.save_timer:
                self.root.after_cancel(self.save_timer)
            self._do_save_undo_state()
        
        if len(self.undo_stack) > 0:
            try:
                self.undo_in_progress = True
                
                # Сохраняем текущее состояние в redo
                self.redo_stack.append(self.last_saved_text)
                
                # Восстанавливаем предыдущее состояние
                previous_text = self.undo_stack.pop()
                self.last_saved_text = previous_text
                
                # Сохраняем позицию курсора перед обновлением
                try:
                    cursor_pos = self.text_area.index(tk.INSERT)
                except:
                    cursor_pos = "1.0"
                
                # Обновляем текстовое поле
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", previous_text)
                
                # Восстанавливаем позицию курсора
                try:
                    self.text_area.mark_set(tk.INSERT, cursor_pos)
                    self.text_area.see(tk.INSERT)
                except:
                    pass
            finally:
                self.undo_in_progress = False
        else:
            self.show_notification("⚠ Нечего отменять")
    
    def redo(self):
        """Повторить отменённое действие"""
        if len(self.redo_stack) > 0:
            try:
                self.undo_in_progress = True
                
                # Сохраняем текущее состояние в undo
                self.undo_stack.append(self.last_saved_text)
                
                # Восстанавливаем следующее состояние
                next_text = self.redo_stack.pop()
                self.last_saved_text = next_text
                
                # Сохраняем позицию курсора
                try:
                    cursor_pos = self.text_area.index(tk.INSERT)
                except:
                    cursor_pos = "1.0"
                
                # Обновляем текстовое поле
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", next_text)
                
                # Восстанавливаем позицию курсора
                try:
                    self.text_area.mark_set(tk.INSERT, cursor_pos)
                    self.text_area.see(tk.INSERT)
                except:
                    pass
            finally:
                self.undo_in_progress = False
        else:
            self.show_notification("⚠ Нечего повторять")
    
    def add_accent(self):
        """Добавляем знак ударения"""
        self.text_area.insert(tk.INSERT, '\u0301')
        self.save_undo_state(force=True)
    
    def smart_copy(self):
        """Умное копирование: выделенный текст или весь текст"""
        try:
            # Если есть выделение - копируем его
            if self.text_area.tag_ranges(tk.SEL):
                self.copy_selected_text()
            else:
                # Иначе копируем весь текст
                self.copy_text()
        except:
            self.show_notification("✗ Ошибка копирования")
    
    def copy_text(self):
        """Копируем весь текст в буфер обмена"""
        text = self.text_area.get("1.0", tk.END).strip()
        try:
            pyperclip.copy(text)
            self.show_notification("✓ Весь текст скопирован!")
        except:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.show_notification("✓ Весь текст скопирован!")
            except:
                self.show_notification("✗ Ошибка копирования")
    
    def copy_selected_text(self):
        """Копируем выделенный текст в буфер обмена"""
        try:
            # Проверяем есть ли выделение
            if self.text_area.tag_ranges(tk.SEL):
                selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                try:
                    pyperclip.copy(selected_text)
                    self.show_notification("✓ Скопировано!")
                except:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                    self.show_notification("✓ Скопировано!")
            else:
                self.show_notification("✗ Нет выделения")
        except:
            self.show_notification("✗ Ошибка копирования")
    
    def cut_text(self):
        """Вырезаем выделенный текст в буфер обмена"""
        try:
            # Проверяем есть ли выделение
            if self.text_area.tag_ranges(tk.SEL):
                selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                
                # Копируем в буфер
                try:
                    pyperclip.copy(selected_text)
                except:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                
                # Удаляем выделенный текст
                self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.save_undo_state(force=True)
                self.show_notification("✓ Вырезано!")
            else:
                self.show_notification("✗ Нет выделения")
        except:
            self.show_notification("✗ Ошибка вырезания")
    
    def select_all_text(self):
        """Выделяем весь текст"""
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
        self.show_notification("✓ Всё выделено!")
    
    def paste_text(self):
        """Вставляем текст из буфера обмена"""
        try:
            # Пытаемся получить через pyperclip
            text = pyperclip.paste()
        except:
            try:
                # Если не получилось - через tkinter
                text = self.root.clipboard_get()
            except:
                self.show_notification("✗ Буфер обмена пуст")
                return
        
        if text:
            # Вставляем в позицию курсора
            self.text_area.insert(tk.INSERT, text)
            self.save_undo_state(force=True)
            self.show_notification("✓ Текст вставлен!")
        else:
            self.show_notification("✗ Буфер обмена пуст")
    
    def clear_text(self):
        """Очищает текстовое поле"""
        if self.is_modified:
            response = messagebox.askyesno(
                "Подтверждение",
                "Есть несохранённые изменения. Очистить текст?",
                icon='warning'
            )
            if not response:
                return
        
        self.text_area.delete("1.0", tk.END)
        # Очищаем стеки undo/redo
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.last_saved_text = "\n"
        self.is_modified = False
        self.current_file = None
        
        # ОПТИМИЗАЦИЯ: Отменяем pending сохранение
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
            self.save_timer = None
            self.pending_save = False
        
        self.update_title()
    
    def open_file(self):
        """Открывает файл"""
        if self.is_modified:
            if not self.ask_save_changes():
                return
        
        file_path = filedialog.askopenfilename(
            title="Открыть текстовый файл",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                self.undo_in_progress = True
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.undo_in_progress = False
                
                # Очищаем стеки undo/redo
                self.undo_stack.clear()
                self.redo_stack.clear()
                self.last_saved_text = self.text_area.get("1.0", tk.END)
                self.current_file = file_path
                self.is_modified = False
                self.text_area.edit_modified(False)
                
                # Отменяем pending сохранение
                if self.save_timer:
                    self.root.after_cancel(self.save_timer)
                    self.save_timer = None
                    self.pending_save = False
                
                self.update_title()
                self.show_notification("✓ Файл открыт!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def save_file(self):
        """Сохраняет файл"""
        if self.current_file:
            file_path = self.current_file
        else:
            file_path = filedialog.asksaveasfilename(
                title="Сохранить текстовый файл",
                defaultextension=".txt",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
        
        if file_path:
            try:
                content = self.text_area.get("1.0", tk.END).strip()
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.current_file = file_path
                self.is_modified = False
                self.text_area.edit_modified(False)
                self.update_title()
                self.show_notification("✓ Файл сохранён!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def on_text_modified(self, event=None):
        """Обработчик изменения текста"""
        if self.text_area.edit_modified():
            self.is_modified = True
            self.update_title()
            self.text_area.edit_modified(False)
    
    def update_title(self):
        """Обновляет заголовок окна"""
        title = "Virtual Keyboard Plus"
        if self.current_file:
            import os
            filename = os.path.basename(self.current_file)
            title = f"{filename} - {title}"
        if self.is_modified:
            title = "* " + title
        self.root.title(title)
    
    def ask_save_changes(self):
        """Спрашивает о сохранении изменений"""
        response = messagebox.askyesnocancel(
            "Сохранить изменения?",
            "Документ был изменён. Сохранить изменения?",
            icon='question'
        )
        
        if response is True:
            self.save_file()
            return True
        elif response is False:
            return True
        else:
            return False
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        # ОПТИМИЗАЦИЯ: Отменяем все pending таймеры
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        
        if self.is_modified:
            if self.ask_save_changes():
                self.root.destroy()
        else:
            self.root.destroy()
    
    def show_notification(self, message):
        """Показывает уведомление"""
        notification = tk.Label(
            self.root, text=message, font=("Arial", 12, "bold"),
            bg="#10b981", fg="white", padx=20, pady=10,
            relief=tk.RAISED, bd=2
        )
        notification.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.root.after(1500, notification.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualKeyboard(root)
    root.mainloop()
