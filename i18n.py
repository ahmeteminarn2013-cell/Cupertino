#!/usr/bin/env python3
"""Cupertino — basit çoklu dil (i18n) modülü.

Sistem dilini (LANG / LC_MESSAGES) algılar, desteklenmeyen dilde İngilizce'ye düşer.
Kullanım:
    from i18n import t
    t("dock")  -> "Dock" / "Док" / ...
"""
import os

# Desteklenen diller: en, tr, es, de, fr, ru, pt, zh
STRINGS = {
    # ---- Control Panel (Ayar Merkezi) ----
    "app_title":    {"en": "Cupertino Settings", "tr": "Cupertino Ayar Merkezi", "es": "Ajustes de Cupertino",
                     "de": "Cupertino-Einstellungen", "fr": "Réglages Cupertino", "ru": "Настройки Cupertino",
                     "pt": "Configurações Cupertino", "zh": "Cupertino 设置"},
    "sec_top":      {"en": "Top Bar (Menu Bar)", "tr": "Üst Panel (Menü Çubuğu)", "es": "Barra superior (menú)",
                     "de": "Obere Leiste (Menüleiste)", "fr": "Barre supérieure (menu)", "ru": "Верхняя панель (меню)",
                     "pt": "Barra superior (menu)", "zh": "顶栏（菜单栏）"},
    "sec_dock":     {"en": "Dock", "tr": "Dock", "es": "Dock", "de": "Dock", "fr": "Dock", "ru": "Док",
                     "pt": "Dock", "zh": "程序坞"},
    "sec_blur":     {"en": "Frosted Glass (Blur)", "tr": "Buzlu Cam (Blur)", "es": "Cristal esmerilado (desenfoque)",
                     "de": "Milchglas (Unschärfe)", "fr": "Verre dépoli (flou)", "ru": "Матовое стекло (размытие)",
                     "pt": "Vidro fosco (desfoque)", "zh": "毛玻璃（模糊）"},
    "transparency": {"en": "Transparency", "tr": "Transparanlık", "es": "Transparencia", "de": "Transparenz",
                     "fr": "Transparence", "ru": "Прозрачность", "pt": "Transparência", "zh": "透明度"},
    "height":       {"en": "Height", "tr": "Yükseklik", "es": "Altura", "de": "Höhe", "fr": "Hauteur",
                     "ru": "Высота", "pt": "Altura", "zh": "高度"},
    "dock_bg":      {"en": "Background opacity", "tr": "Arka plan koyuluğu", "es": "Opacidad del fondo",
                     "de": "Hintergrund-Deckkraft", "fr": "Opacité du fond", "ru": "Непрозрачность фона",
                     "pt": "Opacidade do fundo", "zh": "背景不透明度"},
    "dock_size":    {"en": "Dock size", "tr": "Dock boyutu", "es": "Tamaño del dock", "de": "Dock-Größe",
                     "fr": "Taille du dock", "ru": "Размер дока", "pt": "Tamanho do dock", "zh": "程序坞大小"},
    "corner":       {"en": "Corner radius", "tr": "Köşe yuvarlaklığı", "es": "Radio de esquina",
                     "de": "Eckenradius", "fr": "Rayon des coins", "ru": "Скругление углов",
                     "pt": "Raio dos cantos", "zh": "圆角半径"},
    "preview":      {"en": "Window preview", "tr": "Pencere önizleme", "es": "Vista previa de ventana",
                     "de": "Fenstervorschau", "fr": "Aperçu de fenêtre", "ru": "Предпросмотр окна",
                     "pt": "Pré-visualização", "zh": "窗口预览"},
    "preview_size": {"en": "Preview size", "tr": "Önizleme boyutu", "es": "Tamaño de vista previa",
                     "de": "Vorschaugröße", "fr": "Taille de l'aperçu", "ru": "Размер предпросмотра",
                     "pt": "Tamanho da prévia", "zh": "预览大小"},
    "autohide":     {"en": "Auto-hide", "tr": "Otomatik gizle", "es": "Ocultar automáticamente",
                     "de": "Automatisch ausblenden", "fr": "Masquer automatiquement", "ru": "Автоскрытие",
                     "pt": "Ocultar automaticamente", "zh": "自动隐藏"},
    "blur_on":      {"en": "Blur enabled", "tr": "Blur açık", "es": "Desenfoque activado", "de": "Unschärfe an",
                     "fr": "Flou activé", "ru": "Размытие вкл", "pt": "Desfoque ativado", "zh": "启用模糊"},
    "blur_strength":{"en": "Blur strength", "tr": "Blur şiddeti", "es": "Intensidad del desenfoque",
                     "de": "Unschärfestärke", "fr": "Intensité du flou", "ru": "Сила размытия",
                     "pt": "Intensidade do desfoque", "zh": "模糊强度"},
    "ready":        {"en": "Ready", "tr": "Hazır", "es": "Listo", "de": "Bereit", "fr": "Prêt",
                     "ru": "Готово", "pt": "Pronto", "zh": "就绪"},
    "needs_frosted":{"en": "applies in Frosted style", "tr": "Buzlu stilinde geçerli",
                     "es": "se aplica en estilo Esmerilado", "de": "gilt im Milchglas-Stil",
                     "fr": "s'applique au style Dépoli", "ru": "действует в стиле «Матовый»",
                     "pt": "aplica-se no estilo Fosco", "zh": "在毛玻璃样式下生效"},
    "style":        {"en": "Style", "tr": "Stil", "es": "Estilo", "de": "Stil", "fr": "Style",
                     "ru": "Стиль", "pt": "Estilo", "zh": "样式"},
    "st_frosted":   {"en": "Frosted", "tr": "Buzlu", "es": "Esmerilado", "de": "Milchglas",
                     "fr": "Dépoli", "ru": "Матовый", "pt": "Fosco", "zh": "毛玻璃"},
    "st_dark":      {"en": "Dark", "tr": "Koyu", "es": "Oscuro", "de": "Dunkel", "fr": "Sombre",
                     "ru": "Тёмный", "pt": "Escuro", "zh": "深色"},
    "st_light":     {"en": "Light", "tr": "Açık", "es": "Claro", "de": "Hell", "fr": "Clair",
                     "ru": "Светлый", "pt": "Claro", "zh": "浅色"},
    "st_transp":    {"en": "Clear", "tr": "Şeffaf", "es": "Transp.", "de": "Klar", "fr": "Transp.",
                     "ru": "Прозр.", "pt": "Transp.", "zh": "透明"},
    # ---- Control Center (Kontrol Merkezi) ----
    "darkmode":     {"en": "Dark Mode", "tr": "Karanlık Mod", "es": "Modo oscuro", "de": "Dunkelmodus",
                     "fr": "Mode sombre", "ru": "Тёмный режим", "pt": "Modo escuro", "zh": "深色模式"},
    "on":           {"en": "On", "tr": "Açık", "es": "Activado", "de": "Ein", "fr": "Activé",
                     "ru": "Вкл", "pt": "Ligado", "zh": "开"},
    "off":          {"en": "Off", "tr": "Kapalı", "es": "Desactivado", "de": "Aus", "fr": "Désactivé",
                     "ru": "Выкл", "pt": "Desligado", "zh": "关"},
    "display":      {"en": "Display", "tr": "Ekran", "es": "Pantalla", "de": "Bildschirm", "fr": "Écran",
                     "ru": "Экран", "pt": "Tela", "zh": "显示"},
    "sound":        {"en": "Sound", "tr": "Ses", "es": "Sonido", "de": "Ton", "fr": "Son",
                     "ru": "Звук", "pt": "Som", "zh": "声音"},
    "not_playing":  {"en": "Not playing", "tr": "Çalmıyor", "es": "Nada en reproducción", "de": "Keine Wiedergabe",
                     "fr": "Aucune lecture", "ru": "Ничего не играет", "pt": "Nada tocando", "zh": "未播放"},
}


def _detect() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "")
        if val:
            code = val.split(":")[0].split(".")[0].split("_")[0].lower()
            if code in ("en", "tr", "es", "de", "fr", "ru", "pt", "zh"):
                return code
    return "en"


LANG = _detect()


def t(key: str) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(LANG) or entry.get("en") or key
