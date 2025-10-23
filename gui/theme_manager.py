"""
Theme Manager for Worklog Manager Application

Handles theme application, color schemes, and visual customization.
Supports light/dark modes and custom color configurations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Tuple
from enum import Enum
import json
import os

class ThemeColors:
    """Color definitions for different themes."""
    
    LIGHT_THEME = {
        'bg_primary': '#ffffff',
        'bg_secondary': '#f5f5f5',
        'bg_tertiary': '#e8e8e8',
        'fg_primary': '#2c2c2c',
        'fg_secondary': '#666666',
        'fg_accent': '#0066cc',
        'border': '#cccccc',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'info': '#17a2b8',
        'button_bg': '#f8f9fa',
        'button_active': '#e9ecef',
        'button_fg': '#1a1a1a',
        'entry_bg': '#ffffff',
        'entry_fg': '#2c2c2c',
        'selected': '#007bff',
        'selected_text': '#ffffff'
    }
    
    DARK_THEME = {
        'bg_primary': '#161b26',
        'bg_secondary': '#1f2532',
        'bg_tertiary': '#2a3142',
        'fg_primary': '#f4f7fb',
        'fg_secondary': '#9ea8c2',
        'fg_accent': '#7fb2ff',
        'border': '#313a4c',
        'success': '#45d890',
        'warning': '#f7c75a',
        'danger': '#f26f7c',
        'info': '#63c6f5',
        'button_bg': '#2f3a52',
        'button_active': '#3a4660',
        'button_fg': '#e8ecf4',
        'entry_bg': '#1d2432',
        'entry_fg': '#f4f7fb',
        'selected': '#556bff',
        'selected_text': '#f4f7fb'
    }
    
    HIGH_CONTRAST = {
        'bg_primary': '#0e111b',
        'bg_secondary': '#161a27',
        'bg_tertiary': '#1f2434',
        'fg_primary': '#ffffff',
        'fg_secondary': '#c5cae0',
        'fg_accent': '#ffb454',
        'border': '#ffffff',
        'success': '#4ff29a',
        'warning': '#ffd166',
        'danger': '#ff6b6b',
        'info': '#4ad9ff',
        'button_bg': '#1d2433',
        'button_active': '#263044',
        'button_fg': '#ffffff',
        'entry_bg': '#141926',
        'entry_fg': '#ffffff',
        'selected': '#ffb454',
        'selected_text': '#11131d'
    }

class ThemeManager:
    """Manages application themes and styling."""
    
    def __init__(self, root: tk.Tk, initial_theme: str = 'light'):
        self.root = root
        self.current_theme = initial_theme
        self.custom_themes = {}
        self.styled_widgets = []
        
        # Load custom themes if they exist (before applying colors)
        self.load_custom_themes()
        
        # Apply initial background color immediately to prevent flash
        colors = self.get_theme_colors(initial_theme)
        self.root.configure(bg=colors['bg_primary'])
        
        # Configure ttk styles
        self.style = ttk.Style()
        self._initialize_base_theme()
        self.configure_ttk_styles()

    def _initialize_base_theme(self):
        """Select a ttk theme that allows color customization.
        
        Prefers light-themed bases when using light theme to avoid dark flashes.
        """
        try:
            available = set(self.style.theme_names())
            
            # Select base theme based on current theme preference
            if self.current_theme == 'dark' or self.current_theme == 'high_contrast':
                # For dark themes, prefer dark bases
                preferred = ('sun-valley-dark', 'azure', 'clam', 'alt', 'sun-valley')
            else:
                # For light themes, prefer light bases to avoid dark flashing
                preferred = ('sun-valley', 'azure', 'clam', 'alt')
            
            for candidate in preferred:
                if candidate in available:
                    self.style.theme_use(candidate)
                    return
        except Exception:
            pass  # Fall back to whichever theme ttk already selected
    
    def load_custom_themes(self):
        """Load custom themes from file."""
        themes_file = os.path.join('data', 'custom_themes.json')
        if os.path.exists(themes_file):
            try:
                with open(themes_file, 'r') as f:
                    self.custom_themes = json.load(f)
            except Exception as e:
                print(f"Error loading custom themes: {e}")
    
    def save_custom_themes(self):
        """Save custom themes to file."""
        os.makedirs('data', exist_ok=True)
        themes_file = os.path.join('data', 'custom_themes.json')
        try:
            with open(themes_file, 'w') as f:
                json.dump(self.custom_themes, f, indent=2)
        except Exception as e:
            print(f"Error saving custom themes: {e}")
    
    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """Get color dictionary for specified theme."""
        if theme_name is None:
            theme_name = self.current_theme
        
        if theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        elif theme_name == 'light':
            return ThemeColors.LIGHT_THEME
        elif theme_name == 'dark':
            return ThemeColors.DARK_THEME
        elif theme_name == 'high_contrast':
            return ThemeColors.HIGH_CONTRAST
        else:
            return ThemeColors.LIGHT_THEME
    
    def apply_theme(self, theme_name: str):
        """Apply theme to all registered widgets."""
        self.current_theme = theme_name
        colors = self.get_theme_colors(theme_name)
        
        # Clean up destroyed widgets first
        self.clean_up_destroyed_widgets()
        
        # Apply to root window
        self.root.configure(bg=colors['bg_primary'])
        
        # Update ttk styles
        self.update_ttk_styles(colors)
        
        # Apply to all registered widgets
        for widget_info in self.styled_widgets:
            self.apply_widget_theme(widget_info['widget'], widget_info['style'], colors)
    
    def apply_fonts(self, font_family: str = "Arial", font_size: int = 10):
        """Apply font settings globally to the entire application.
        
        Args:
            font_family: Font family name (e.g., 'Arial', 'Helvetica')
            font_size: Base font size in points
        """
        # Configure default fonts for tk widgets
        default_font = (font_family, font_size)
        bold_font = (font_family, font_size, 'bold')
        
        # Update tk default fonts
        self.root.option_add("*Font", default_font)
        self.root.option_add("*Label.Font", default_font)
        self.root.option_add("*Button.Font", default_font)
        self.root.option_add("*Entry.Font", default_font)
        self.root.option_add("*Text.Font", default_font)
        self.root.option_add("*Listbox.Font", default_font)
        self.root.option_add("*Menu.Font", default_font)
        self.root.option_add("*Menubutton.Font", default_font)
        
        # Update ttk styles with fonts
        self.style.configure('TLabel', font=default_font)
        self.style.configure('TButton', font=default_font)
        self.style.configure('Themed.TButton', font=default_font)
        self.style.configure('TEntry', font=default_font)
        self.style.configure('TCheckbutton', font=default_font)
        self.style.configure('TRadiobutton', font=default_font)
        self.style.configure('TCombobox', font=default_font)
        self.style.configure('Treeview', font=default_font)
        self.style.configure('Treeview.Heading', font=bold_font)
        self.style.configure('TNotebook.Tab', font=default_font)
        self.style.configure('TLabelframe', font=default_font)
        self.style.configure('TLabelframe.Label', font=bold_font)
        self.style.configure('TSpinbox', font=default_font)
        
        # Force update all widgets recursively
        self._update_widget_fonts_recursive(self.root, font_family, font_size)
    
    def _update_widget_fonts_recursive(self, widget, font_family: str, font_size: int):
        """Recursively update fonts for all widgets in the tree.
        
        Args:
            widget: Root widget to start from
            font_family: Font family name
            font_size: Base font size
        """
        try:
            # Try to update the widget's font if it has one
            if hasattr(widget, 'configure') or hasattr(widget, 'config'):
                try:
                    # Check if widget has a font option
                    current_font = widget.cget('font') if hasattr(widget, 'cget') else None
                    if current_font:
                        # Preserve bold/italic if present
                        if isinstance(current_font, tuple) and len(current_font) >= 3:
                            new_font = (font_family, font_size, current_font[2])
                        elif isinstance(current_font, str) and 'bold' in current_font.lower():
                            new_font = (font_family, font_size, 'bold')
                        else:
                            new_font = (font_family, font_size)
                        widget.configure(font=new_font)
                except (tk.TclError, AttributeError):
                    pass  # Widget doesn't support font configuration
            
            # Recursively process children
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    self._update_widget_fonts_recursive(child, font_family, font_size)
        except Exception:
            pass  # Ignore any errors during font update
    
    def configure_ttk_styles(self):
        """Configure initial ttk styles."""
        colors = self.get_theme_colors()
        self.update_ttk_styles(colors)
    
    def update_ttk_styles(self, colors: Dict[str, str]):
        """Update ttk styles with current theme colors."""

        disabled_bg = self.darken_color(colors['button_bg'], 0.85)
        
        # Use explicit button_fg if available, otherwise calculate contrast
        button_text_color = colors.get('button_fg', self.get_contrast_text_color(colors['button_bg'], colors))

        self.style.configure(
            'Themed.TButton',
            background=colors['button_bg'],
            foreground=button_text_color,
            bordercolor=colors['border'],
            borderwidth=0,
            padding=(10, 6),
            relief='flat'
        )

        self.style.map(
            'Themed.TButton',
            background=[
                ('pressed', colors['selected']),
                ('active', colors['button_active']),
                ('disabled', disabled_bg)
            ],
            foreground=[('disabled', colors['fg_secondary'])]
        )

        self.style.configure(
            'TButton',
            background=colors['button_bg'],
            foreground=button_text_color,
            bordercolor=colors['border'],
            borderwidth=0,
            padding=(10, 6),
            relief='flat'
        )

        self.style.map(
            'TButton',
            background=[
                ('pressed', colors['selected']),
                ('active', colors['button_active']),
                ('disabled', disabled_bg)
            ],
            foreground=[('disabled', colors['fg_secondary'])]
        )

        def configure_action_button(style_name: str, base_color: str, text_color: str = None):
            """Configure a custom action button style with consistent states."""
            if not text_color:
                # Calculate contrast text color based on button background brightness
                text_color = self.get_contrast_text_color(base_color, colors)

            active_color = self.lighten_color(base_color, 1.08)
            pressed_color = self.darken_color(base_color, 0.9)

            self.style.configure(
                style_name,
                background=base_color,
                foreground=text_color,
                bordercolor=colors['border'],
                borderwidth=0,
                padding=(10, 6),
                relief='flat'
            )

            self.style.map(
                style_name,
                background=[
                    ('pressed', pressed_color),
                    ('active', active_color),
                    ('disabled', disabled_bg)
                ],
                foreground=[('disabled', colors['fg_secondary'])]
            )

        # Custom control button palettes
        configure_action_button('StartDay.TButton', colors['success'])
        configure_action_button('EndDay.TButton', colors['danger'])
        stop_base = self.lighten_color(colors['warning'], 1.15)
        configure_action_button('Stop.TButton', stop_base)
        continue_base = self.lighten_color(colors['success'], 1.35)
        configure_action_button('Continue.TButton', continue_base)

        self.style.configure(
            'Themed.TFrame',
            background=colors['bg_primary'],
            bordercolor=colors['border'],
            borderwidth=0
        )

        # Also update default frame style for consistency
        self.style.configure(
            'TFrame',
            background=colors['bg_primary'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'Themed.TLabel',
            background=colors['bg_primary'],
            foreground=colors['fg_primary']
        )

        self.style.configure(
            'TLabel',
            background=colors['bg_primary'],
            foreground=colors['fg_primary']
        )

        self.style.configure(
            'Themed.TEntry',
            fieldbackground=colors['entry_bg'],
            foreground=colors['entry_fg'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'TEntry',
            fieldbackground=colors['entry_bg'],
            foreground=colors['entry_fg'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'Themed.TLabelframe',
            background=colors['bg_primary'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'Themed.TLabelframe.Label',
            background=colors['bg_primary'],
            foreground=colors['fg_primary']
        )

        self.style.configure(
            'TLabelframe',
            background=colors['bg_primary'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'TLabelframe.Label',
            background=colors['bg_primary'],
            foreground=colors['fg_primary']
        )

        self.style.configure(
            'Themed.Treeview',
            background=colors['bg_secondary'],
            foreground=colors['fg_primary'],
            fieldbackground=colors['bg_secondary'],
            bordercolor=colors['border'],
            borderwidth=0,
            rowheight=24
        )

        self.style.configure(
            'Treeview',
            background=colors['bg_secondary'],
            foreground=colors['fg_primary'],
            fieldbackground=colors['bg_secondary'],
            bordercolor=colors['border'],
            rowheight=24
        )

        self.style.map(
            'Themed.Treeview',
            background=[('selected', colors['selected'])],
            foreground=[('selected', colors['selected_text'])]
        )

        self.style.map(
            'Treeview',
            background=[('selected', colors['selected'])],
            foreground=[('selected', colors['selected_text'])]
        )

        self.style.configure(
            'Themed.Treeview.Heading',
            background=colors['bg_tertiary'],
            foreground=colors['fg_primary'],
            bordercolor=colors['border'],
            borderwidth=0,
            padding=(8, 6)
        )

        self.style.configure(
            'Treeview.Heading',
            background=colors['bg_tertiary'],
            foreground=colors['fg_primary'],
            bordercolor=colors['border'],
            padding=(8, 6)
        )

        self.style.map(
            'Themed.Treeview.Heading',
            background=[('active', colors['button_active'])]
        )

        self.style.map(
            'Treeview.Heading',
            background=[('active', colors['button_active'])]
        )

        self.style.configure(
            'Themed.TNotebook',
            background=colors['bg_primary'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'TNotebook',
            background=colors['bg_primary'],
            bordercolor=colors['border']
        )

        self.style.configure(
            'Themed.TNotebook.Tab',
            background=colors['bg_secondary'],
            foreground=colors['fg_primary'],
            bordercolor=colors['border'],
            padding=(12, 6)
        )

        self.style.configure(
            'TNotebook.Tab',
            background=colors['bg_secondary'],
            foreground=colors['fg_primary'],
            bordercolor=colors['border'],
            padding=(12, 6)
        )

        self.style.map(
            'Themed.TNotebook.Tab',
            background=[
                ('selected', colors['bg_primary']),
                ('active', colors['bg_tertiary'])
            ],
            foreground=[
                ('selected', colors['fg_primary']),
                ('disabled', colors['fg_secondary'])
            ]
        )

        self.style.map(
            'TNotebook.Tab',
            background=[
                ('selected', colors['bg_primary']),
                ('active', colors['bg_tertiary'])
            ],
            foreground=[
                ('selected', colors['fg_primary']),
                ('disabled', colors['fg_secondary'])
            ]
        )

        # Make checkbuttons and radiobuttons match the palette
        self.style.configure(
            'TCheckbutton',
            background=colors['bg_primary'],
            foreground=colors['fg_primary'],
            bordercolor=colors['border'],
            focuscolor=colors['selected'],
            indicatorbackground=colors['button_bg'],
            indicatorforeground=colors['selected'],
            indicatorrelief='flat'
        )

        self.style.map(
            'TCheckbutton',
            background=[('active', colors['bg_secondary'])],
            foreground=[('disabled', colors['fg_secondary'])],
            indicatorforeground=[
                ('selected', colors['selected']),
                ('!selected', colors['fg_secondary'])
            ],
            indicatorbackground=[
                ('selected', colors['button_bg']),
                ('!selected', colors['button_bg'])
            ]
        )

        self.style.configure(
            'TRadiobutton',
            background=colors['bg_primary'],
            foreground=colors['fg_primary'],
            bordercolor=colors['border'],
            focuscolor=colors['selected'],
            indicatorbackground=colors['button_bg'],
            indicatorforeground=colors['selected'],
            indicatorrelief='flat'
        )

        self.style.map(
            'TRadiobutton',
            background=[('active', colors['bg_secondary'])],
            foreground=[('disabled', colors['fg_secondary'])],
            indicatorforeground=[
                ('selected', colors['selected']),
                ('!selected', colors['fg_secondary'])
            ],
            indicatorbackground=[
                ('selected', colors['button_bg']),
                ('!selected', colors['button_bg'])
            ]
        )

        self.style.configure(
            'TCombobox',
            fieldbackground=colors['entry_bg'],
            background=colors['entry_bg'],
            foreground=colors['entry_fg'],
            arrowcolor=colors['fg_secondary'],
            bordercolor=colors['border']
        )

        readonly_bg = colors['entry_bg']
        disabled_bg = self.darken_color(colors['entry_bg'], 0.9)

        self.style.map(
            'TCombobox',
            fieldbackground=[
                ('readonly', readonly_bg),
                ('disabled', disabled_bg)
            ],
            foreground=[('disabled', colors['fg_secondary'])],
            background=[('disabled', disabled_bg)]
        )

        # TSpinbox styling
        self.style.configure(
            'TSpinbox',
            fieldbackground=colors['entry_bg'],
            background=colors['entry_bg'],
            foreground=colors['entry_fg'],
            arrowcolor=colors['fg_secondary'],
            bordercolor=colors['border']
        )

        self.style.map(
            'TSpinbox',
            fieldbackground=[('disabled', disabled_bg)],
            foreground=[('disabled', colors['fg_secondary'])],
            background=[('disabled', disabled_bg)]
        )

        self.style.configure(
            'TScrollbar',
            troughcolor=colors['bg_secondary'],
            background=colors['button_bg']
        )

        self.style.map(
            'TScrollbar',
            background=[('active', colors['button_active'])]
        )

        self.style.configure(
            'Horizontal.TScrollbar',
            troughcolor=colors['bg_secondary'],
            background=colors['button_bg']
        )

        self.style.map(
            'Horizontal.TScrollbar',
            background=[('active', colors['button_active'])]
        )
    
    def register_widget(self, widget: tk.Widget, style: str = 'default'):
        """Register a widget for theme updates."""
        widget_info = {
            'widget': widget,
            'style': style
        }
        self.styled_widgets.append(widget_info)
        
        # Apply current theme immediately
        colors = self.get_theme_colors()
        self.apply_widget_theme(widget, style, colors)
    
    def apply_widget_theme(self, widget: tk.Widget, style: str, colors: Dict[str, str]):
        """Apply theme to a specific widget."""
        try:
            # Check if widget still exists and is valid
            if not widget or not hasattr(widget, 'winfo_exists'):
                return
                
            # Check if widget has been destroyed
            try:
                if not widget.winfo_exists():
                    return
            except tk.TclError:
                # Widget has been destroyed
                return
                
            widget_class = widget.__class__.__name__
            
            # Check if it's a TTK widget - better detection method
            is_ttk_widget = widget_class.startswith('Ttk') or 'ttk' in str(type(widget).__module__)
            
            if style == 'primary_bg':
                if is_ttk_widget:
                    # TTK widgets need style configuration, skip for now
                    pass
                else:
                    widget.configure(bg=colors['bg_primary'], fg=colors['fg_primary'])
            elif style == 'secondary_bg':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(bg=colors['bg_secondary'], fg=colors['fg_primary'])
            elif style == 'tertiary_bg':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(bg=colors['bg_tertiary'], fg=colors['fg_primary'])
            elif style == 'button':
                if is_ttk_widget:
                    # TTK buttons use style configuration
                    pass
                else:
                    widget.configure(
                        bg=colors['button_bg'],
                        fg=colors['fg_primary'],
                        activebackground=colors['button_active'],
                        activeforeground=colors['fg_primary'],
                        relief='flat',
                        bd=0,
                        highlightthickness=0
                    )
            elif style == 'success_button':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['success'],
                        fg=colors['selected_text'],
                        activebackground=self.darken_color(colors['success']),
                        activeforeground=colors['selected_text'],
                        relief='flat',
                        bd=0
                    )
            elif style == 'danger_button':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['danger'],
                        fg=colors['selected_text'],
                        activebackground=self.darken_color(colors['danger']),
                        activeforeground=colors['selected_text'],
                        relief='flat',
                        bd=0
                    )
            elif style == 'entry':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['entry_bg'],
                        fg=colors['entry_fg'],
                        insertbackground=colors['fg_primary'],
                        selectbackground=colors['selected'],
                        selectforeground=colors['selected_text']
                    )
            elif style == 'text':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_secondary'],
                        fg=colors['fg_primary'],
                        insertbackground=colors['fg_primary'],
                        selectbackground=colors['selected'],
                        selectforeground=colors['selected_text']
                    )
            elif style == 'listbox':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_secondary'],
                        fg=colors['fg_primary'],
                        selectbackground=colors['selected'],
                        selectforeground=colors['selected_text']
                    )
            elif style == 'menu':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_secondary'],
                        fg=colors['fg_primary'],
                        activebackground=colors['selected'],
                        activeforeground=colors['selected_text']
                    )
            elif style == 'label':
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_primary'],
                        fg=colors['fg_primary']
                    )
            elif style == 'highlighted_bg':
                # Special highlighted background for current session frame
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_tertiary'],
                        relief='ridge',
                        bd=1
                    )
            elif style == 'highlighted_label':
                # Label on highlighted background
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_tertiary'],
                        fg=colors['fg_primary']
                    )
            elif style == 'highlighted_accent_label':
                # Accented label on highlighted background
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_tertiary'],
                        fg=colors['fg_accent']
                    )
            elif style == 'break_lunch_bg':
                # Lunch break frame background
                if is_ttk_widget:
                    pass
                else:
                    bg_color = self.blend_colors(colors['bg_secondary'], colors['warning'], 0.10)
                    widget.configure(
                        bg=bg_color,
                        relief='ridge',
                        bd=1
                    )
            elif style == 'break_lunch_label':
                # Label for lunch breaks
                if is_ttk_widget:
                    pass
                else:
                    bg_color = self.blend_colors(colors['bg_secondary'], colors['warning'], 0.10)
                    widget.configure(
                        bg=bg_color,
                        fg=colors['fg_primary']
                    )
            elif style == 'break_coffee_bg':
                # Coffee break frame background
                if is_ttk_widget:
                    pass
                else:
                    bg_color = self.blend_colors(colors['bg_secondary'], colors['info'], 0.08)
                    widget.configure(
                        bg=bg_color,
                        relief='ridge',
                        bd=1
                    )
            elif style == 'break_coffee_label':
                # Label for coffee breaks
                if is_ttk_widget:
                    pass
                else:
                    bg_color = self.blend_colors(colors['bg_secondary'], colors['info'], 0.08)
                    widget.configure(
                        bg=bg_color,
                        fg=colors['fg_primary']
                    )
            elif style == 'break_general_bg':
                # General break frame background
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_secondary'],
                        relief='ridge',
                        bd=1
                    )
            elif style == 'break_general_label':
                # Label for general breaks
                if is_ttk_widget:
                    pass
                else:
                    widget.configure(
                        bg=colors['bg_secondary'],
                        fg=colors['fg_primary']
                    )
            else:  # default
                if hasattr(widget, 'configure') and not is_ttk_widget:
                    widget.configure(bg=colors['bg_primary'], fg=colors['fg_primary'])
            
            # Handle border colors for widgets that support it (avoid TTK widgets)
            if (hasattr(widget, 'configure') and not is_ttk_widget and 
                hasattr(widget, 'keys') and 'highlightbackground' in widget.keys()):
                widget.configure(highlightbackground=colors['border'])
                
        except tk.TclError:
            # Widget has been destroyed or is invalid, silently ignore
            pass
        except Exception as e:
            # Only print errors that aren't about destroyed widgets
            error_msg = str(e).lower()
            if 'invalid command name' not in error_msg and 'has been destroyed' not in error_msg:
                print(f"Error applying theme to widget: {e}")
    
    def darken_color(self, color: str, factor: float = 0.8) -> str:
        """Darken a color by the given factor."""
        if color.startswith('#'):
            color = color[1:]
        
        try:
            # Convert hex to RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Darken each component
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color
    
    def lighten_color(self, color: str, factor: float = 1.2) -> str:
        """Lighten a color by the given factor."""
        if color.startswith('#'):
            color = color[1:]
        
        try:
            # Convert hex to RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Lighten each component
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color

    def blend_colors(self, color1: str, color2: str, factor: float = 0.5) -> str:
        """Blend two colors together.
        
        Args:
            color1: First color (hex)
            color2: Second color (hex)
            factor: Blend factor (0.0 = all color1, 1.0 = all color2)
        
        Returns:
            Blended color as hex string
        """
        if color1.startswith('#'):
            color1 = color1[1:]
        if color2.startswith('#'):
            color2 = color2[1:]
        
        try:
            # Convert hex to RGB
            r1 = int(color1[0:2], 16)
            g1 = int(color1[2:4], 16)
            b1 = int(color1[4:6], 16)
            
            r2 = int(color2[0:2], 16)
            g2 = int(color2[2:4], 16)
            b2 = int(color2[4:6], 16)
            
            # Blend
            r = int(r1 * (1 - factor) + r2 * factor)
            g = int(g1 * (1 - factor) + g2 * factor)
            b = int(b1 * (1 - factor) + b2 * factor)
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color1 if color1 else color2

    def get_contrast_text_color(self, background_color: str, colors: Dict[str, str]) -> str:
        """Choose a contrasting text color based on background brightness."""
        hex_color = background_color.lstrip('#')

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

            # For lighter backgrounds, use dark text
            # For darker backgrounds, use light text
            if luminance > 0.5:
                return '#1a1a1a'  # Dark text for light backgrounds
            else:
                return colors.get('selected_text', '#ffffff')  # Light text for dark backgrounds
        except Exception:
            return '#1a1a1a'
    
    def create_custom_theme(self, name: str, base_theme: str = 'light', 
                          color_overrides: Dict[str, str] = None):
        """Create a custom theme based on an existing theme."""
        base_colors = self.get_theme_colors(base_theme)
        custom_colors = base_colors.copy()
        
        if color_overrides:
            custom_colors.update(color_overrides)
        
        self.custom_themes[name] = custom_colors
        self.save_custom_themes()
    
    def clean_up_destroyed_widgets(self):
        """Remove destroyed widgets from the styled_widgets list."""
        valid_widgets = []
        for widget_info in self.styled_widgets:
            widget = widget_info['widget']
            try:
                if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                    valid_widgets.append(widget_info)
            except tk.TclError:
                # Widget has been destroyed, skip it
                pass
        self.styled_widgets = valid_widgets
    
    def get_available_themes(self) -> list:
        """Get list of all available themes."""
        themes = ['light', 'dark', 'high_contrast']
        themes.extend(list(self.custom_themes.keys()))
        return themes
    
    def delete_custom_theme(self, name: str) -> bool:
        """Delete a custom theme."""
        if name in self.custom_themes:
            del self.custom_themes[name]
            self.save_custom_themes()
            return True
        return False
    
    def export_theme(self, theme_name: str, file_path: str):
        """Export a theme to a file."""
        theme_data = {
            'name': theme_name,
            'colors': self.get_theme_colors(theme_name)
        }
        
        with open(file_path, 'w') as f:
            json.dump(theme_data, f, indent=2)
    
    def import_theme(self, file_path: str) -> bool:
        """Import a theme from a file."""
        try:
            with open(file_path, 'r') as f:
                theme_data = json.load(f)
            
            name = theme_data.get('name', 'imported_theme')
            colors = theme_data.get('colors', {})
            
            if colors:
                self.custom_themes[name] = colors
                self.save_custom_themes()
                return True
        except Exception as e:
            print(f"Error importing theme: {e}")
        
        return False

class ThemePreview:
    """Widget for previewing themes before applying them."""
    
    def __init__(self, parent: tk.Widget, theme_manager: ThemeManager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.preview_widgets = []
        
        # Get current theme colors to apply immediately
        colors = self.theme_manager.get_theme_colors()
        
        self.preview_frame = tk.Frame(parent, bg=colors['bg_primary'])
        self.preview_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_preview_elements()
        
        # Apply current theme immediately to all preview widgets
        self.update_preview(self.theme_manager.current_theme)
    
    def create_preview_elements(self):
        """Create sample elements for theme preview."""
        # Get current theme colors
        colors = self.theme_manager.get_theme_colors()
        
        # Title
        title_label = tk.Label(self.preview_frame, text="Theme Preview", 
                              font=('Arial', 14, 'bold'),
                              bg=colors['bg_primary'], fg=colors['fg_primary'])
        title_label.pack(pady=(0, 10))
        
        # Buttons frame
        buttons_frame = tk.Frame(self.preview_frame, bg=colors['bg_primary'])
        buttons_frame.pack(fill='x', pady=5)
        
        # Sample buttons
        normal_btn = tk.Button(buttons_frame, text="Normal Button",
                              bg=colors['button_bg'], fg=colors['fg_primary'],
                              relief='flat', bd=0, highlightthickness=0)
        normal_btn.pack(side='left', padx=5)
        
        success_btn = tk.Button(buttons_frame, text="Success Button",
                               bg=colors['success'], fg=colors['selected_text'],
                               relief='flat', bd=0)
        success_btn.pack(side='left', padx=5)
        
        danger_btn = tk.Button(buttons_frame, text="Danger Button",
                              bg=colors['danger'], fg=colors['selected_text'],
                              relief='flat', bd=0)
        danger_btn.pack(side='left', padx=5)
        
        # Entry field
        entry_frame = tk.Frame(self.preview_frame, bg=colors['bg_primary'])
        entry_frame.pack(fill='x', pady=5)
        
        entry_label = tk.Label(entry_frame, text="Sample Entry:",
                              bg=colors['bg_primary'], fg=colors['fg_primary'])
        entry_label.pack(side='left')
        sample_entry = tk.Entry(entry_frame,
                               bg=colors['entry_bg'], fg=colors['entry_fg'],
                               insertbackground=colors['fg_primary'])
        sample_entry.pack(side='left', padx=(5, 0), fill='x', expand=True)
        sample_entry.insert(0, "Sample text input")
        
        # Text area
        text_frame = tk.Frame(self.preview_frame, bg=colors['bg_primary'])
        text_frame.pack(fill='both', expand=True, pady=5)
        
        text_label = tk.Label(text_frame, text="Sample Text Area:",
                             bg=colors['bg_primary'], fg=colors['fg_primary'])
        text_label.pack(anchor='w')
        sample_text = tk.Text(text_frame, height=4,
                             bg=colors['bg_secondary'], fg=colors['fg_primary'],
                             insertbackground=colors['fg_primary'])
        sample_text.pack(fill='both', expand=True)
        sample_text.insert('1.0', "This is a sample text area\nShowing how text appears\nIn the selected theme")

        # Keep track of widgets for preview styling only
        self.preview_widgets.extend([
            (self.preview_frame, 'primary_bg'),
            (title_label, 'label'),
            (buttons_frame, 'primary_bg'),
            (normal_btn, 'button'),
            (success_btn, 'success_button'),
            (danger_btn, 'danger_button'),
            (entry_frame, 'primary_bg'),
            (entry_label, 'label'),
            (sample_entry, 'entry'),
            (text_frame, 'primary_bg'),
            (text_label, 'label'),
            (sample_text, 'text')
        ])
    
    def update_preview(self, theme_name: str):
        """Update preview with specified theme."""
        colors = self.theme_manager.get_theme_colors(theme_name)
        for widget, style in self.preview_widgets:
            self.theme_manager.apply_widget_theme(widget, style, colors)